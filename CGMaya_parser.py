
#coding=utf-8
import array
import functools
import itertools
import string
import struct, os.path
import sys
import ctypes
import subprocess
import copy

import CGMaya_config

_is_printable = set(string.printable).difference(string.whitespace).__contains__


class Encoder(object):
    def split(self, encoded, size_hint):
        for i in xrange(0, len(encoded), size_hint):
            yield encoded[i:i + size_hint]

    def repr_chunk(self, chunk):
        """Create string representation of a chunk returned from :meth:`split`."""
        return ''.join(c if _is_printable(c) else '.' for c in chunk)

class StructEncoder(Encoder):

    def __init__(self, format_char):
        self.format_char = format_char
        self.size = struct.Struct('>' + format_char).size

    def split(self, encoded, size_hint):
        size_hint = size_hint - (size_hint % self.size)
        return super(StructEncoder, self).split(encoded, size_hint)

    def unpack(self, encoded):
        count, rem = divmod(len(encoded), self.size)
        if rem:
            raise ValueError('encoded length %d is not multiple of %d; %d remains' % (len(encoded), self.size, rem))
        return struct.unpack('>%d%s' % (count, self.format_char), encoded)

    def repr_chunk(self, encoded):
        return ' '.join(repr(x) for x in self.unpack(encoded))


class StringEncoder(Encoder):

    def split(self, encoded, size_hint):
        return encoded.rstrip('\0').split('\0')

    def repr_chunk(self, chunk):
        return repr(chunk)


# Map encoding names to the object which exposes the Encoder interface.
encoders = {}


def register_encoder(names, encoder=None):
    if isinstance(names, basestring):
        names = [names]
    if encoder is None:
        return functools.partial(register_encoder, names)
    else:
        for name in names:
            encoders[name] = encoder
        return encoder


register_encoder('float', StructEncoder('f'))
register_encoder('uint', StructEncoder('L'))
register_encoder('string', StringEncoder())

#: Map tag names to the name of an encoding. Add to this dict to interpret tags
#: as certain types.
tag_encoding = {

    # Maya headers.
    'VERS': 'string',  # app version
    'UVER': 'string',
    'MADE': 'string',
    'CHNG': 'string',  # timestamp
    'ICON': 'string',
    'INFO': 'string',
    'OBJN': 'string',
    'INCL': 'string',
    'LUNI': 'string',  # linear unit
    'TUNI': 'string',  # time unit
    'AUNI': 'string',  # angle unit
    'FINF': 'string',  # file info

    # Generic.
    'SIZE': 'uint',

    # DAG
    'CREA': 'string',  # create node
    'STR ': 'string',  # string attribute

    # Cache headers.
    'VRSN': 'string',  # cache version
    'STIM': 'uint',  # cache start time
    'ETIM': 'uint',  # cache end time

    # Cache channels.
    'CHNM': 'string',  # channel name

    # Cache data.
    'FBCA': 'float',  # floating cache array

}


def get_encoder(tag):
    encoding = tag_encoding.get(tag, 'raw')
    return encoders.get(encoding) or Encoder()


def hexdump(*args, **kwargs):
    return ''.join(_hexdump(*args, **kwargs))


def _hexdump(raw, initial_offset=0, chunk=4, line=16, indent='', tag=None):
    chunk2 = 2 * chunk
    line2 = 2 * line
    encoder = get_encoder(tag)
    offset = initial_offset

    for encoded_chunk in encoder.split(raw, line):
        if not encoded_chunk:
            continue

        yield indent
        yield '%04x: ' % offset
        offset += len(encoded_chunk)

        # Encode the chunk to hex, pad it, and chunk it further.
        hex_chunk = encoded_chunk.encode('hex')
        hex_chunk += ' ' * (line2 - len(hex_chunk))
        for i in xrange(0, len(hex_chunk), chunk2):
            yield '%s ' % hex_chunk[i:i + chunk2]

        yield encoder.repr_chunk(encoded_chunk)
        yield '\n'


_group_tags = set()
_tag_alignments = {}

for base in ('FORM', 'CAT ', 'LIST', 'PROP'):
    for char, alignment in (('', 2), ('4', 4), ('8', 8)):
        tag = base[:-len(char)] + char if char else base
        _group_tags.add(tag)
        _tag_alignments[tag] = alignment


def _group_is_64bit(tag):
    return _tag_alignments.get(tag) == 8


def _get_tag_alignment(tag):
    return _tag_alignments.get(tag, 2)


def _get_padding(size, alignment):
    if size % alignment == 0:
        return 0
    else:
        return alignment - size % alignment

def isChinese(ustring):
    for item in ustring:
        try:
            if u'\u4e00' <= item <= u'\u9fff':
                return True
        except UnicodeDecodeError:
            return True
    return False


class Node(object):

    def __init__(self):

        #: The children of this node.
        self.children = []

    def add_child(self, child):
        self.children.append(child)
        child.parent = self
        return child

    def add_group(self, *args, **kwargs):
        return self.add_child(Group(*args, **kwargs))

    def add_chunk(self, *args, **kwargs):
        return self.add_child(Chunk(*args, **kwargs))

    def find(self, tag):
        """Iterate across all descendants of this node with a given tag."""
        for child in self.children:
            if child.tag == tag:
                yield child
            if isinstance(child, Node):
                for x in child.find(tag):
                    yield x

    def find_one(self, tag, *args):

        for child in self.find(tag):
            return child
        if args:
            return args[0]
        raise KeyError(tag)

    def walk(self):
        yield self
        for child in self.children:
            for x in child.walk():
                yield x

    def dumps_iter(self):

        for child in self.children:
            for x in child.dumps_iter():
                yield x


class Group(Node):

    def __init__(self, tag, type_='FOR4', size=0, start=0):
        super(Group, self).__init__()

        #: The group type (e.g. ``FORM``, ``LIST``, ``PROP``, ``CAT``).
        self.type = type_

        self.size = size
        self.start = start

        #: The data type.
        self.tag = tag

        self.alignment = _get_tag_alignment(self.type)
        self.end = self.start + self.size + _get_padding(self.size, self.alignment)

    def pprint(self, data, _indent=0):
        """Print a structured representation of the group to stdout."""
        tag = self.tag if self.tag.isalnum() else '0x' + self.tag.encode('hex')
        #print '  start =', self.start
        crea = self.children[0] if (self.children and self.children[0].tag == 'CREA') else None
        name = crea.data.split('\0')[0][1:] if crea else None
        name = ' "%s"' % name if name else ''
        #print _indent * '    ' + ('%s group%s (%s); %d bytes for %d children:' % (
        #tag, name, self.type, self.size, len(self.children)))
        for child in self.children:
            child.pprint(data=data, _indent=_indent + 1)

    def dumps_iter(self):
        output = []
        for child in self.children:
            output.extend(child.dumps_iter())
        r = self.type
        yield self.type
        #yield struct.pack(">L", sum(len(x) for x in output) + 4)
        der = struct.pack(">Q", sum(len(x) for x in output) + 4)
        yield struct.pack(">Q", sum(len(x) for x in output) + 4)
        t = self.tag
        yield self.tag
        for x in output:
            yield x

    def setOther(self, other):
        self.other = other


class Chunk(object):

    def __init__(self, tag, data='', offset=None, **kwargs):
        self.parent = None

        #: The data type.
        self.tag = tag

        #: Raw binary data.
        self.data = data

        self.offset = offset
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def walk(self):
        yield self

    def pprint(self, data, _indent):
        """Print a structured representation of the node to stdout."""
        encoding = tag_encoding.get(self.tag)
        if encoding:
            header = '%d bytes as %s(s)' % (len(self.data), encoding)
        else:
            header = '%d raw bytes' % len(self.data)

        #print '              ', self.string, self.offset
        #print _indent * '    ' + ('%s; %s' % (self.tag, header))

        if data:
            #print hexdump(self.data, self.offset, tag=self.tag, indent=(_indent + 1) * '    ').rstrip()
            pass

    def __repr__(self):
        return '<%s %s; %d bytes>' % (self.__class__.__name__, self.tag, len(self.data))

    def dumps_iter(self):
        yield self.tag
        #yield struct.pack(">L", len(self.data))
        yield struct.pack(">Q", len(self.data))
        yield self.data
        padding = _get_padding(len(self.data), self.parent.alignment)
        if padding:
            yield '\0' * padding

    def _unpack(self, format_char):
        element_size = struct.calcsize('>' + format_char)
        if len(self.data) % element_size:
            raise ValueError('%s is not multiple of %d for %r format' % (len(self.data), element_size, format_char))
        format_string = '>%d%s' % (len(self.data) / element_size, format_char)
        unpacked = struct.unpack(format_string, self.data)
        return array.array(format_char, unpacked)

    def _pack(self, format_char, values):
        self.data = struct.pack('>%d%s' % (len(values), format_char), *values)

    @property
    def ints(self):
        """Binary data interpreted as array of unsigned integers.

        This is settable to an iterable of integers."""
        return self._unpack('L')

    @ints.setter
    def ints(self, values):
        self._pack('L', values)

    @property
    def floats(self):
        """Binary data interpreted as array of floats.

        This is settable to an iterable of floats."""
        return self._unpack('f')

    @floats.setter
    def floats(self, values):
        self._pack('f', values)

    @property
    def string(self):
        """Binary data interpreted as a string.

        This is settable with a string."""
        return self.data.rstrip('\0')

    @string.setter
    def string(self, v):
        self.data = str(v).rstrip('\0') + '\0'

class Parser(Node):
    """Maya binary file parser.

    :param file: The file-like object to parse from; must support ``read(size)``
        and ``tell()``.

    """

    def __init__(self, file):
        super(Parser, self).__init__()

        self._file = file
        self._group_stack = []
        self._is_64bit = None

        self.children = []

    def close(self):
        self._file.close()

    def walk(self):
        yield self
        for child in self.children:
            for x in child.walk():
                yield x

    def pprint(self, data, _indent=-1):
        """Print a structured representation of the file to stdout."""
        for child in self.children:
            child.pprint(data, _indent=_indent + 1)

    def _read_int(self):
        if self._is_64bit:
            return struct.unpack(">Q", self._file.read(8))[0]
        else:
            return struct.unpack(">L", self._file.read(4))[0]

    def parse_next(self):
        while self._group_stack and self._group_stack[-1].end <= self._file.tell():
            self._group_stack.pop(-1)
        tag = self._file.read(4)
        if not tag:
            return

        if self._is_64bit is None:
            if tag == 'FOR8':
                self._is_64bit = True
            elif tag == 'FOR4':
                self._is_64bit = False
            else:
                CGMaya_config.logger.error('            Invalid magic tag---\%r\r' % tag)
                raise ValueError('Invalid magic tag.', tag)
        if self._is_64bit:
            other = self._file.read(4)
        offset = self._file.tell()
        size = self._read_int()
        if tag in _group_tags:
            group_tag = self._file.read(4)
            group = Group(group_tag, tag, size, offset)
            group.setOther(other)
            # Add it as a child of the current group.
            group_head = self._group_stack[-1] if self._group_stack else self
            group_head.add_child(group)
            self._group_stack.append(group)
            return group
        else:
            if True:
                try:
                    data = self._file.read(size)
                except OverflowError:
                    CGMaya_config.logger.error('            OverflowError %d, %r\r' % (self._file.tell() - size, data))
                    pass

            else:
                data = ''
                self._file.seek(size, 1)

            chunk = Chunk(tag, data, offset)

            assert self._group_stack, 'Data chunk outside of group.'
            self._group_stack[-1].add_child(chunk)

            # Cleanup padding.
            padding = _get_padding(size, self._group_stack[-1].alignment)
            if padding:
                self._file.read(padding)
            return chunk

    def parse_all(self):
        """Parse the entire (remaining) file."""
        while self.parse_next() is not None:
            pass

class mayaAscii(object):
    def __init__(self, fileName_in):
        self.assetName = ''
        self.projectDir = ''
        self.refProjectDir = ''
        self.lines = []
        self.fileName_in = fileName_in
        self.fp_in = None
        self.fp_out = None
        self.refAssetList = []
        self.textureList = []

    def _isRefAsset(self, line):
        return line.find('file -rdi') >= 0 or \
               line.find('file -r -ns') >= 0 or \
               line.find('file -r -rpr') >= 0

    def _isTexture(self, line):
        return line.find('setAttr ".ftn" -type "string"') >= 0 or\
               line.find('setAttr ".fn" -type "string"') >= 0 or \
               line.find('setAttr ".filename" -type "string"') >= 0 or\
               line.find('setAttr ".tex0" -type "string"') >= 0

    def processRefFile(self, line):
        refList = line.split('"')
        tmp = refList.pop()
        srcRefPath = refList.pop()
        #print 'srcRefPath =', srcRefPath
        if srcRefPath.find('.ma') <= 0 and srcRefPath.find('.mb') <= 0:
            CGMaya_config.logger.warning('          srcRefPath---%s\r' % srcRefPath)
            return
        refName = os.path.basename(srcRefPath)
        if (refName.find('chr_') < 0) and\
                (refName.find('loc_') < 0) and \
                (refName.find('pro_') < 0) and \
                (refName.find('lt_') < 0) and \
                (refName.find('vfx_') < 0) and \
                (refName.find('oth_') < 0):
            destRefPath = self.projectDir + '/' + refName.split('.')[0] + '/' + refName
        else:
            destRefPath = self.refProjectDir + '/' + refName.split('.')[0] + '/' + refName
        if not destRefPath in self.refAssetList:
            self.refAssetList.append(destRefPath)
            CGMaya_config.logger.debug('    RefPath---%s, %s\r' % (srcRefPath, destRefPath))
        #self.line2 = list[0] + ' -typ "' + refList[1] + '" "' + destRefPath + '";\n'
        self.line2 = line.replace(srcRefPath, destRefPath)
        self.line2 = self.line2 + '\n'
        self.fp_out.write(self.line2)

    def processTextureFile(self, line):
        wordList = line.split('";')
        leftStrList = wordList[0].split(' "string" "')
        texturePath = leftStrList.pop()
        texturePath1 = texturePath
        if texturePath.find('.') < 0:
            line = line + '\n'
            self.fp_out.write(line)
            return
        if texturePath.find('.<udim>.') > 0 or texturePath.find('.<UDIM>.') > 0:
            fffn = os.path.basename(texturePath)
            ttfn = fffn.split('.')[0]
            refPath = os.path.dirname(texturePath)
            for root, dirs, nFiles in os.walk(refPath):
                for ffn in nFiles:
                    if ffn.find(ttfn) >= 0:
                        fPath = os.path.join(root, ffn)
                        if not fPath in self.textureList:
                            self.textureList.append(fPath)
        else:
            if not texturePath in self.textureList:
                self.textureList.append(texturePath)
        textureName = os.path.basename(texturePath)
        fn = self.projectDir + '/' + os.path.basename(self.assetName)
        if not os.path.exists(fn):
            os.mkdir(fn)
        texturePath = fn + '/' + CGMaya_config.CGMaya_Texture_Dir
        if not os.path.exists(texturePath):
            os.mkdir(texturePath)
        texturePath = texturePath + '/' + textureName
        #CGMaya_config.logger.debug('    TexturePath---%s, %s\r' % (texturePath1, texturePath))
        self.line2 = leftStrList[0] + ' "string" "' + texturePath + '";\n'
        self.fp_out.write(self.line2)

    def getFilePath(self):
        self.fp_in = open(self.fileName_in, 'r')
        lines = self.fp_in.readlines()
        n = 0
        while n < len(lines):
            line = lines[n].strip()
            if self._isRefAsset(line):
                while not line.endswith(";"):
                    n = n + 1
                    line1 = lines[n]
                    line1.replace('\t', ' ')
                    line1 = line1.strip()
                    line = line + line1
                refList = line.split('"')
                tmp = refList.pop()
                srcRefPath = refList.pop()
                if not srcRefPath in self.refAssetList:
                    self.refAssetList.append(srcRefPath)
            elif self._isTexture(line):
                while not line.endswith(";"):
                    n = n + 1
                    line1 = lines[n]
                    line1.replace('\t', ' ')
                    line1 = line1.strip()
                    line = line + line1
                texturePath = line.split('"')[5]
                if not texturePath in self.textureList:
                    self.textureList.append(texturePath)
            n = n + 1
        self.fp_in.close()
        return self.refAssetList, self.textureList

    def setAssetName(self, assetName):
        self.assetName = assetName

    def replaceFilePath(self, assetName, fileName_out, projectDir, refProjectDir):
        self.assetName = assetName
        self.projectDir = projectDir
        self.refProjectDir = refProjectDir
        CGMaya_config.logger.debug("projectDir-----%s, %s\r" % (projectDir, refProjectDir))
        if not os.path.exists(self.fileName_in):
            CGMaya_config.logger.error('   File is not Exist---%s\r' % self.fileName_in)
            return
        self.fp_in = open(self.fileName_in, 'r')
        self.fp_out = open(fileName_out, "w")
        lines = self.fp_in.readlines()
        n = 0
        while n < len(lines):
            line = lines[n].strip()
            if self._isRefAsset(line):
                while not line.endswith(";"):
                    n = n + 1
                    line1 = lines[n]
                    line1.replace('\t', ' ')
                    line1 = line1.strip()
                    line = line + line1
                self.processRefFile(line)
            elif self._isTexture(line):
                while not line.endswith(";"):
                    n = n + 1
                    line1 = lines[n]
                    line1.replace('\t', ' ')
                    line1 = line1.strip()
                    line = line + line1
                self.processTextureFile(line)
            else:
                self.fp_out.write(lines[n])
            n = n + 1
        self.fp_in.close()
        self.fp_out.close()
        return self.refAssetList, self.textureList

    def writeMayaFile(self, fileName_out):
        with open(fileName_out, 'w') as fp:
            for line in self.lines:
                fp.write(line)

class mayaBinary(object):
    def __init__(self, fileName_in):
        self.assetName = ''
        self.projectDir = ''
        self.refProjectDir = ''
        self.delta = 0
        self.pos = 0
        self.fp = None
        self.groupStart = 0
        self.refAssetList = []
        self.textureList = []
        if fileName_in.find('.mb') < 0:
            return
        if not os.path.exists(fileName_in):
            return
        self.parser = Parser(open(fileName_in, 'rb'))
        self.parser.parse_all()

    def _isRefAsset(self, child):
        return child.tag == 'FRDI' or child.tag == 'FREF'

    def _isTexture(self, child, group):
        return child.tag == 'STR ' and (group.tag == 'RTFT' or \
                        group.tag == 'REFN' or group.tag == 'AUDI' or \
                        group.tag == '\x00\x11\xa9\x02' or group.tag == '\x00\x11\xa9\x64')

    def _processRef(self, chunk):
        if chunk.string.find('.ma') > 0:
            filePath = chunk.string.split('.ma')[0] + '.ma'
            ext = '.ma'
        elif chunk.string.find('.mb') > 0:
            filePath = chunk.string.split('.mb')[0] + '.mb'
            ext = '.mb'
        else:
            CGMaya_config.logger.error('   refFilePath is error---%s\r' % chunk.string)
            return 0
        if not filePath in self.refAssetList:
            self.refAssetList.append(filePath)
        refName = os.path.basename(filePath)
        if (refName.find('chr_') < 0) and (refName.find('loc_') < 0) and (refName.find('pro_') < 0) and (refName.find('lt_') < 0):
            destRefPath = self.projectDir + '/' + refName.split('.')[0] + '/' + refName
        else:
            destRefPath = self.refProjectDir + '/' + refName.split('.')[0] + '/' + refName
        #destRefPath = self.refProjectDir + '/' + refName.split('.')[0] + '/' + refName
        destRefPath1 = destRefPath
        if not os.path.exists(destRefPath):
            destRefPath = destRefPath1.split('.')[0] + ext
            if not os.path.exists(destRefPath):
                CGMaya_config.logger.error('   destRefPath is not Exist---%s %s\r' % (destRefPath1, destRefPath))
        CGMaya_config.logger.debug('    RefPath---%s, %s\r' % (filePath, destRefPath))
        if len(destRefPath) > len(filePath):
            size = len(chunk.data) + len(destRefPath) - len(filePath)
            paddingIn = _get_padding(len(chunk.data), 8)
            paddingOut = _get_padding(size, 8)
            delta = size - len(chunk.data) + paddingOut - paddingIn
        else:
            size = len(chunk.data)
            delta = 0
        destStr = ctypes.create_string_buffer(size)
        offset = 0
        if chunk.tag == 'FRDI':
            struct.pack_into('>4s', destStr, 0, filePath[0:4])
            offset = 4
        fmt = '>' + str(len(destRefPath)) + 's'
        struct.pack_into(fmt, destStr, offset, str(destRefPath))
        fmt = '>' + str(size - offset - len(destRefPath)) + 's'
        struct.pack_into(fmt, destStr, offset + len(destRefPath), chunk.data[len(filePath):])
        chunk.data = destStr
        return delta

    def _processTexture(self, chunk):
        fstr = chunk.string.split(' ')[0]
        if fstr.find('ftn') < 0 and fstr.find('fn') < 0 and fstr.find('tex0') < 0:
            return 0
        path = chunk.string.split('\x00')[1]
        preStr = chunk.string.split('\x00')[0]
        nn = len(preStr)
        if not path in self.textureList:
            self.textureList.append(path)
        fn = self.projectDir + '/' + os.path.basename(self.assetName)
        #print 'fn =', fn
        if not os.path.exists(fn):
            os.mkdir(fn)
        texturePath1 = fn + '/' + CGMaya_config.CGMaya_Texture_Dir
        #print 'texturePATH1 =', texturePath1
        if not os.path.exists(texturePath1):
            os.mkdir(texturePath1)
        if isChinese(texturePath1):
            CGMaya_config.logger.warning('    HANZI-------%s\r' % texturePath1)
            uipath = unicode(texturePath1, "utf8")
            texturePath1 = uipath
        destPath = texturePath1 + '/' + os.path.basename(path)
        CGMaya_config.logger.debug('    TexturePath---%s, %s\r' % (path, destPath))
        nn = nn + 1
        if len(destPath) > len(path):
            #size = 5 + len(destPath)
            size = nn + len(destPath)
            paddingIn = _get_padding(len(chunk.data), 8)
            paddingOut = _get_padding(size, 8)
            delta = size - len(chunk.data) + paddingOut - paddingIn
        else:
            size = len(chunk.data)
            delta = 0
        destStr = ctypes.create_string_buffer(size)
        fmt1 = '>' + str(nn) + 's'
        #struct.pack_into('>4s', destStr, 0, chunk.data[0:4])
        struct.pack_into(fmt1, destStr, 0, chunk.data[0:nn])
        fmt = '>' + str(len(destPath)) + 's'
        #struct.pack_into(fmt, destStr, 5, str(destPath))
        struct.pack_into(fmt, destStr, nn, str(destPath))
        chunk.data = destStr
        return delta

    def _writeGroup(self, group):
        self.fp.seek(group.start - 8)
        self.fp.write(struct.pack('4s4s', group.type, group.other))
        self.fp.write(struct.pack('>Q4s', group.size, group.tag))

    def _processParent(self, parent, delta):
        while isinstance(parent, Group):
            parent.size += delta
            self.fp.seek(parent.start)
            self.fp.write(struct.pack('>Q', parent.size))
            parent = parent.parent

    def _processParent_no(self, parent):
        while isinstance(parent, Group):
            parent = parent.parent

    def getFilePath(self):
        rootGroup = self.parser.children[0]
        for group in rootGroup.children:
            childList = []
            for child in group.children:
                childList.append(child)
            child = childList.pop(0)
            while child:
                if isinstance(child, Group):
                    for subChild in child.children:
                        childList.append(subChild)
                else:
                    if self._isRefAsset(child):
                        if child.string.find('.ma') > 0:
                            filePath = child.string.split('.ma')[0] + '.ma'
                            ext = '.ma'
                        elif child.string.find('.mb') > 0:
                            filePath = child.string.split('.mb')[0] + '.mb'
                            ext = '.mb'
                        else:
                            CGMaya_config.logger.error('   refFilePath is error---%s\r' % child.string)
                            return '', ''
                        if not filePath in self.refAssetList:
                            self.refAssetList.append(filePath)
                        self._processParent_no(child.parent)
                    elif self._isTexture(child, group):
                        fstr = child.string.split('\x00')[0]
                        if fstr.find('ftn') < 0 and fstr.find('fn') < 0 and fstr.find('tex0') < 0:
                            return 0
                        path = child.string.split('\x00')[1]
                        if not path in self.textureList:
                            self.textureList.append(path)
                        self._processParent_no(child.parent)
                if len(childList) == 0:
                    child = None
                else:
                    child = childList.pop(0)
        return self.refAssetList, self.textureList

    def replaceFilePath(self, assetName, fileName_out, projectDir, refProjectDir):
        self.assetName = assetName
        self.projectDir = projectDir
        self.refProjectDir = refProjectDir
        self.delta = 0
        with open(fileName_out, 'wb') as self.fp:
            rootGroup = self.parser.children[0]
            self._writeGroup(rootGroup)
            for group in rootGroup.children:
                group.start += self.delta
                group.end += self.delta
                self._writeGroup(group)
                childList = []
                for child in group.children:
                    childList.append(child)
                child = childList.pop(0)
                while child:
                    if isinstance(child, Group):
                        child.start += self.delta
                        child.end += self.delta
                        self._writeGroup(child)
                        for subChild in child.children:
                            childList.append(subChild)
                    else:
                        child.offset += self.delta
                        if self._isRefAsset(child):
                            delta = self._processRef(child)
                            self.delta += delta
                            self._processParent(child.parent, delta)
                        elif self._isTexture(child, group):
                            delta = self._processTexture(child)
                            self.delta += delta
                            self._processParent(child.parent, delta)
                        self.fp.seek(child.offset - 8)
                        self.fp.write(struct.pack('4si', child.tag, 0))
                        self.fp.write(struct.pack('>Q', len(child.data)))
                        self.fp.write(child.data)
                    if len(childList) == 0:
                        child = None
                    else:
                        child = childList.pop(0)
            self.fp.write(struct.pack('i', 0))
        return self.refAssetList, self.textureList

def mayaParser(fileName):
    if fileName.find('.ma') >= 0:
        return mayaAscii(fileName)
    elif fileName.find('.mb') >= 0:
        return mayaBinary(fileName)

class processRedshiftProxyFile(object):
    def __init__(self, fileName_in, fileName_out=None):
        self.fileName_in = fileName_in
        self.fileName_out = fileName_out
        self.fileSize = os.path.getsize(fileName_in)
        self.fp_in = open(self.fileName_in, "rb")
        if self.fileName_out == None:
            self.fp_out = None
        else:
            self.fp_out = open(self.fileName_out, "wb")

        self.refFileList = []
        self.seekFileList = []

    def replaceFilePath(self):
        buffer = self.fp_in.read(self.fileSize)
        dir = os.path.dirname(self.fileName_in)
        for item in CGMaya_config.fileEXTNameList:
            #buffer = str(buffer).lower()
            pos = buffer.find(item)
            if pos < 0:
                continue
            destBuffer = ctypes.create_string_buffer(self.fileSize)
            curPos = 0
            while pos >= 0:
                n = pos
                while n > 0 and not (ord(buffer[n]) == 0):
                    n = n - 1
                fmt = '>' + str(n + 1 - curPos) + 's'
                struct.pack_into(fmt, destBuffer, curPos, buffer[curPos:n + 1])
                curPos = n + 1
                refFile = buffer[n + 1:pos + 4]
                refFile1 = refFile
                if refFile.find('..') >= 0:
                    dirNums = refFile.count('..')
                    for n in range(0, dirNums):
                        dir = os.path.dirname(dir)
                    refFile3 = dir + refFile.split('..').pop()
                    #refFile3.replace('/', r'\\')
                    refFile2 = './' + os.path.basename(refFile3)
                    refFile2 = str(refFile2)
                else:
                    refFile2 = './' + os.path.basename(refFile)
                refFile = refFile2.replace('\\', '/')
                if not refFile in self.refFileList:
                    self.refFileList.append(refFile)
                refFile2 = refFile2 + chr(0)
                fmt = '>' + str(len(refFile2)) + 's'
                try:
                    struct.pack_into(fmt, destBuffer, curPos, refFile2)
                except Exception, e:
                    print('struct.pack_into Error:', e)
                curPos = pos + 4
                pos = buffer.find(item, pos + 4)
            try:
                fmt = '>' + str(self.fileSize - curPos) + 's'
                struct.pack_into(fmt, destBuffer, curPos, buffer[curPos:self.fileSize])
                fmt = '>' + str(self.fileSize) + 's'
                buffer = struct.unpack(fmt, destBuffer)[0]
            except Exception, e:
                print('struct.pack_into struct.unpack Error:', e)
        self.fp_out.write(buffer)
        self.fp_out.close()
        return self.refFileList

    def getFilePath(self):
        buffer = self.fp_in.read(self.fileSize)
        self.fp_in.close()
        for item in CGMaya_config.fileEXTNameList:
            pos = buffer.find(item)
            while pos >= 0:
                n = pos
                while n > 0 and not (ord(buffer[n]) == 0):
                    n = n - 1
                refFile = buffer[n + 1:pos + 4]
                if refFile.find('..') >= 0:
                    dir = os.path.dirname(self.fileName_in)
                    dirNums = refFile.count('..')
                    for n in range(0, dirNums):
                        dir = os.path.dirname(dir)
                    refFile = dir + refFile.split('..').pop()
                refFile = refFile.replace('\\', '/')
                if not refFile in self.refFileList:
                    self.refFileList.append(refFile)
                pos = buffer.find(item, pos + 4)
        return self.refFileList

rscmdLine_exe = "C:/ProgramData/Redshift/bin/redshiftCmdLine.exe"

def get_proxyInfo_cmd(proxy_file, mode="printdependencies"):
    """
    mode in ["printdependencies" ,"fileinfo"]
    """
    if not os.path.exists(rscmdLine_exe):
        print('RedShiftCmdLine EXE File is not Found！！！！ ')
        return
    texture_info = list()
    run_cmd = rscmdLine_exe + " -" + mode + " " + proxy_file
    p = subprocess.Popen(run_cmd, shell=True, stdout=subprocess.PIPE)

    out, err = p.communicate()
    for line in out.splitlines():
        if line:
            texture_info.append(line)
    return texture_info

#test = mayaParser('D://gb.ma')
#refAssetList = textureList = test.getFilePath()

