# 在linux下编译exe文件
## 以gmp举例
1、需要安装mingw  
2、在gmp解压后的文件夹内使用`.\configure`生成makefile的时候要指定mingw平台 
并且指定安装路径到另外一个文件夹比如（/usr/window/win_gmp），避免和原系统的gmp冲突  
3、`make`以及`make install`完成后，使用mingw编译c源文件时链接win_gmp内的include和lib，最后加上`-lgmp`即可

