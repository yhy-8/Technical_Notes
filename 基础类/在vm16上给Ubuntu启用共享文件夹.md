# 在vm16上给Ubuntu启用共享文件夹
教程(https://zhuanlan.zhihu.com/p/650638983)
## 一、虚拟机外操作：
1、右键虚拟机，进入“虚拟机设置“  
2、在上方选择“选项”  
3、启用“共享文件夹”，设置需要共享的文件夹路径  
## 二、虚拟机内操作：
1、`sudo mount -t fuse.vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other`
（ubuntu18.04.6需要这条命令进行挂载，而ubuntu24.04.1就不需要，提示没有mnt/hgfs可以创建一个）  
2、去到/mnt/hgfs既可