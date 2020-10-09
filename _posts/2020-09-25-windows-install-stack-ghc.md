---
title: 在Windows上安装Haskell
tags:
- Haskell
- 编程
key: 2020-09-25.windows-install-stack-ghc
---

由于本学期北京大学开设《计算概论（A）：函数式程序设计》课程，很多同学在Windows下安装Haskell开发环境遇到困难。这里我们描述在Windows上使用`stack`安装Haskell开发环境的方法。

<!--more-->

## 安装`stack`

这里我们参考[`stack`官方网站](https://docs.haskellstack.org/en/stable/README/)：

> On Windows, you can download and install the [Windows 64-bit Installer](https://get.haskellstack.org/stable/windows-x86_64-installer.exe).

点击上方引文中的链接下载`stack`的安装程序并运行，如无特殊需求，选择默认的安装路径即可。

由于Windows下默认由260字节的路径长度限制，且`stack`管理的文件通常具有较深的目录层次，`stack`建议在Windows下设置`STACK_ROOT=C:\sr`（安装程序的默认选项）。考虑到许多中国用户不喜欢安装在C盘，可以将`STACK_ROOT`改为`D:\sr`等等。
{:.info}

## 使用`stack`安装GHC

`stack`可以用于管理Haskell编译器（GHC）以及Haskell库，这里我们将使用`stack`安装GHC。

### 安装

通常情况下，我们可以使用`stack new`创建新项目，并在编译该项目（`stack build`）时由`stack`自动安装对应版本的GHC。由于是学期初，我们尚未接触到这些内容，这里直接使用下列命令（以下简称`stack setup`）来安装GHC：

```bash
stack --resolver lts-16.15 setup
```

考虑到国内的实际情况，通常建议配置清华源：按照[TUNA Hackage](https://mirrors.tuna.tsinghua.edu.cn/help/hackage/)和[TUNA Stackage](https://mirrors.tuna.tsinghua.edu.cn/help/stackage/)的说明直接配置即可。在写作本文的时间，按上述步骤安装的`stack`版本是`2.3.3`，因此应该对应按照`stack >= v2.1.1`和`stack >= v2.3.1`两节来修改配置文件。
{:.info}

**提示**：TUNA给出的配置文件路径是`%APPDATA%\stack\config.yaml`（要找到这个文件，首先在资源管理器的地址栏中输入`%APPDATA%`，再打开子目录`stack`，即可找到`config.yaml`；如果文件还不存在，可以手动创建）。由于我们修改了`STACK_ROOT`，需要修改的配置文件在`%STACK_ROOT%\config.yaml`，例如按默认的`STACK_ROOT=C:\sr`，全局配置文件就在`C:\sr\config.yaml`。
{:.warning}

**说明**：上述命令中的`--resolver lts-16.15`表示要求`stack`使用[LTS-16.15](https://www.stackage.org/lts-16.15)，这是写作本文时最新的LTS。建议自己到[`Stackage`](https://www.stackage.org)查看最新的LTS。使用这个配置主要是为了避免安装相对比较古老的8.6.5版本，Windows上无法使用的8.8.2版本，以及Windows 2004更新后变得不可用的8.8.3版本。关于这些版本的具体问题，可以查看[GHC的Issues](https://gitlab.haskell.org/ghc/ghc/-/issues)。
{:.info}

### 故障排除

在Windows上用`stack`安装GHC有时会遇到`Permission Denied`错误。尚不清楚这个问题的发生机理，但有绕过该问题的解决方法。我们很容易观察到，`stack`安装GHC的方法是下载一个`.tar.xz`压缩包，并使用下载的`7z.exe`和`7z.dll`来解压文件，最后创建用于标记GHC安装成功的`ghc-X.X.X.installed`文件。

那么，由于`stack`失败的时候完成了下载`.tar.xz`的步骤，可以直接用`7z.exe`解压，并直接用`echo`命令创建标记文件：

```bash
./7z x ghc-8.8.4.tar.xz
./7z x ghc-8.8.4.tar
echo installed>ghc-8.8.4.installed
```

这样，重新运行`stack setup`命令后，就能继续完成随后的步骤了。当然，后续安装MSYS2依旧可能遇到相同问题，我们同样照此办理即可：

```bash
./7z x msys2-20180531.tar.xz
./7z x msys2-20180531.tar
echo installed>msys2-20180531.installed
```

确认安装已经完成（即成功运行一次`stack setup`）后，中间生成的`.tar`文件可以删除来减少空间占用；如果不需要留下原始安装文件以备未来重装，也可以连同`stack`自动下载的`.tar.xz`文件一起删除。这不会影响使用。

**注意**：如果使用了PowerShell的老版本，`>`不能用来重定向命令输出，这时可以使用`echo installed| Out-File ghc-8.8.4.installed`；或者干脆使用文本编辑器把“installed”保存在`ghc-8.8.4.installed`即可。
{:.warning}

## 测试与庆祝

到这里，我们应该已经成功安装了`stack`和GHC。首先，测试一下GHC和GHCi的可用性：

```bash
$ stack exec -- ghc --version
The Glorious Glasgow Haskell Compilation System, version 8.8.4
$ stack exec -- ghci
GHCi, version 8.8.3: https://www.haskell.org/ghc/  :? for help
Prelude> :q
Leaving GHCi.
```

这说明我们已经正确安装了一个可用的GHC和`stack`。

如果希望直接使用`ghc`/`ghci`命令启动GHC/GHCi，可以将它所在路径加入`PATH`。我们首先使用命令`stack exec -- where.exe ghc`得知GHC的所在路径，然后将提示的路径加入`PATH`即可。
{:.info}

尽管给出了上面的方法，但是我们不推荐这么做，因为`stack`可以管理多个版本的GHC（避免冲突），可以使用命令行选项选择GHC版本，例如：`stack --compiler ghc-8.8.4 exec ghci`。
{:.warning}

我们已经在Windows上获得了一个可用的Haskell开发环境了。下面我们就可以放烟花庆祝一下，然后开始愉快地使用GHC开发了。
