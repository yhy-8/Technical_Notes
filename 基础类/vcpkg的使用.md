# vcpkg是c/c++库管理工具，在win系统上非常利于c/c++轻便开发 
vcpkg安装完成后就只是一个名为`vcpkg`的文件夹  
使用其命令安装的库都会被存放在其文件夹下的`installed `   
编译时调用即可

win系统安装命令  
```
cd xxx # 你想安装工具的地方
git clone https://github.com/microsoft/vcpkg
.\vcpkg\bootstrap-vcpkg.bat
```
示例：安装GMP  
`.\vcpkg\vcpkg install gmp:x64-windows`