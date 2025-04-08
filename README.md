游戏《苏丹的游戏》存档管理器

windows环境，release部分下载exe文件直接运行即可。

代码提供：[mskk是真的](https://github.com/CherryC9H13N)

目前问题：

已经完结打出结局的存档，无法回溯到历史回合。

影响这个的因素是global.json和global.bat.json这两个文件，因为这两个文件还存了别的东西 所以不方便用程序完全替换。需要：对比完结存档和未完结存档的这两个文件，具体差别在哪，导致完结存档无法回档。然后，加一个自动修复功能。欢迎贡献。

手动解决方案：

备份一个完结存档，创建新游戏，将新游戏存档中的global.json和global.bat.json替换掉完结存档文件夹中的这两个文件，就可以正常回溯了。


## 截图示例
![UI](https://7s-1304005994.cos.ap-singapore.myqcloud.com/42c50be9-74c8-4c54-ad51-36d704714f67.png)
