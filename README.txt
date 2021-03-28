CGMaya

视觉云CGTeam，基于Maya的插件，基于Python2.7开发。

支持maya 2014, 2015, 2016, 2017, 2018, 2019

部署方式：

    复制方式：

1）git clone https://github.com/gbsdu/CGMaya.git

2）把CGMaya目录拷贝到C:\Users\用户\Documents\maya\版本\scripts

3）把CGMaya目录中的userSetup.mel拷贝到C:\Users\用户\Documents\maya\版本\scripts

4）启动maya,maya的菜单栏上出现CGMenu，按账号“登录”即可。

    拖拽方式：

1) git clone https://github.com/gbsdu/CGMaya.git

2) 启动maya;

3) 把CGmaya目录中的setup.mel拖到maya视窗内;

4）退出maya;

5）重新启动maya,maya的菜单栏上出现CGMenu，按账号“登录”即可。

6）卸载，把目录下的unInstall.mel拖到maya视窗下执行即可。

userSetup.mel:

global proc CGMaya_mel()
{
        python "import CGMaya as CGMaya";
        python "CGMaya.CGMaya_main.app()";
}
CGMaya_mel;
