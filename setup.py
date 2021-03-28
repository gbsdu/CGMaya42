#import setuptools  # important
from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
"""
extensions = []
extensions.append(Extension('dist', ['CGMaya_main.py', 'CGMaya_dialog.py', 'CGMaya_function.py',
			 'CGMaya_parser.py', 'CGMaya_config.py', 'CGMaya_service.py', 'CGMaya_logger.py',
            'RWingForMaya.py', 'RWingRendererIO.py']))
#extensions.append(Extension('subFolder.subModule', ['subFolder/subModule.py']))

setup(
    ext_modules=cythonize(extensions, compiler_directives={'language_level': 4}),

)
"""
setup(ext_modules = cythonize('CGMaya_main.py'))
setup(ext_modules = cythonize('CGMaya_dialog.py'))
setup(ext_modules = cythonize('CGMaya_function.py'))
setup(ext_modules = cythonize('CGMaya_export.py'))
setup(ext_modules = cythonize('CGMaya_parser.py'))
setup(ext_modules = cythonize('CGMaya_submit.py'))
#setup(ext_modules = cythonize('CGMaya_config.py'))
setup(ext_modules = cythonize('CGMaya_service.py'))
setup(ext_modules = cythonize('CGMaya_logger.py'))
setup(ext_modules = cythonize('CGMaya_mouse.py'))
#setup(ext_modules = cythonize('CGMaya_timer.py'))
setup(ext_modules = cythonize('RWingForMaya.py'))
setup(ext_modules = cythonize('RWingRendererIO.py'))