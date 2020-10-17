---
title: Haskell列表生成式
tags:
- Haskell
- 编程
key: 2020-10-09.haskell-list-comprehensions
---

上一周《计算概论（A）：函数式程序设计》课上讲到了列表生成式（list comprehensions），可以理解成是Haskell语言的一个语法糖（syntactic sugar）。这里我们将介绍Haskell 2010 Report[(1)]中给出的一种转译方案（translation strategy），可以用来把一切列表生成式翻译成普通的函数调用结构；此外，我们还将介绍列表生成式的Monad翻译，并介绍GHC的两个扩展：Monad生成式（moand comprehensions）和并行列表生成式（parallel list comprehensions）。

<!--more-->

至于为什么上一周的课我这一周才写博客呢？~~当然是因为我鸽了。~~当然是因为上一周已经写过一篇了，那么这一篇就刚好可以留到这周来写。
{:.success}

值得注意的是，Haskell Report只是给出了一组恒等式，它们可以在编译时用于翻译列表生成式，但并不就表明Haskell编译器只能采取这种转译形式。实际编译过程中，编译器完全可能采取其他方式。
{:.warning}

## 列表生成式的一般形式

**列表生成式**是形如`[ exp | qual₁, ..., qualₙ ]`的表达式（$n \ge 1$），其中`exp`是一个表达式，表达式`qual₁`，……，`qualₙ`称为限定式（qualifier），分为**生成器**（generators，形如`pat <- exp`）、**局部绑定**（local bindings，形如`let pat = exp`）以及**过滤器**（boolean guards，形如`exp`，是任意的布尔类型表达式）。

这里对局部绑定的描述是简化了的。使用关键字`let`可以一次性引入多个绑定，即`let { p₁ = e₁; ...; pₙ = eₙ }`（按代码布局（layout）转译后的结果）。有关代码布局的转译方法，我会在后面的文章中详细写一写，~~欢迎追更~~，也可以直接参看Haskell 2010 Report第12页的layout一节。
{:.warning}

## 转译方案

{% highlight haskell %}
[ e | True ]            = [e]
[ e | q ]               = [ e | q, True ]
[ e | b, Q ]            = if b then [ e | Q ] else []
[ e | p <- l, Q ]       = let ok p = [ e | Q ]
                              ok _ = []
                          in concatMap ok l
[ e | let decls, Q ]    = let decls in [ e | Q ]
{% endhighlight %}

这里，`e`表示任意表达式，`q`表示任意限定式，`b`表示任意布尔表达式，`Q`表示一系列（至少一个）限定式，`p <- l`中`p`是一个自由变量、`l`是任意列表类型的表达式。`let decls`表示一组`let`绑定。
{:.info}

## 转译方案的理解

### 哨兵

首先看转译方案的前两行，我们称之为**哨兵**（guard）：

```haskell
[ e | True ]            = [e]
[ e | q ]               = [ e | q, True ]
```

这保证了所有表达式都以一个过滤器`True`结尾，就避免了繁琐的枚举，保证了后面所有规则中的`Q`都至少匹配到一个限定式。如果不使用这个技巧，后面的规则可能就会变得繁琐得多：以`[ e | b, Q ]`为例，我们必须同时匹配`Q`为空时的`[ e | b ]`和`Q`不空时的`[ e | b, Q ]`。

这是因为，假如`Q`为空，那么我们就不能写`[ e | Q ]`了，因为列表生成式要求至少有一个限定式。
{:.info}

把繁琐的模式整理出通用的形式，在模式匹配时一次性解决，这在写Haskell程序时也是有用的技巧。
{:.success}

### 过滤器

过滤器的语义相当简单，就是仅当条件成立才生成列表。它转译成一个`if`表达式：

```haskell
[ e | b, Q ]            = if b then [ e | Q ] else []
```

### 局部`let`绑定

局部`let`绑定的作用是为表达式引入名字，供后续的限定器`Q`以及代表元`e`使用。它直接转译成一个`let`表达式：

```haskell
[ e | let decls, Q ]    = let decls in [ e | Q ]
```

值得注意的是，这个转译保持了所有绑定的作用域是正确的（`decls`中的所有绑定在`e`和`Q`中可用）。

`let`绑定和生成器都有能力引入新的名字。马上我们就将看到，这个转译方案同样也保持了生成器引入的名字的作用域。由于转译保持了所有这些作用域，整个转译可以看成是单纯的语法变换，这也是列表生成式可以被看成单纯的语法糖的原因。
{:.info}

### 生成器

生成器是所有限定式中最复杂的一个，需要仔细考察它的语义才能理解它的转译方法。生成器`p <- l`的语义可以不严格地列举如下：

- 在列表`l`中遍历元素`x`；
- 在元素`x`上匹配模式`p`;
- 如果模式匹配成功，就将模式`p`中的所有名字引入作用域；

我们可以举例说明：生成器`Just x <- [Just 42, Nothing, Just 0]`会将`x`依次绑定到`42`和`0`。具体说来，首先按顺序取出这列表中的全部三个元素，然后用模式`Just x`匹配，其中第0、2个元素匹配成功，第1个匹配不成功。每一个成功匹配各绑定到`x`一次。
{:.success}

转译规则就是将上面所述的行为形式化：

```haskell
[ e | p <- l, Q ]       = let ok p = [ e | Q ]
                              ok _ = []
                          in concatMap ok l
```

我们一点一点来看。设`l`的类型是`[a]`，即`l`是一个`a`类型元素的列表。那么`ok`就是一个`a -> [b]`的函数，它由一个`a`类型的值计算出结果列表。`concatMap :: (a -> [b]) -> [a] -> [b]`实际上就是`concat . map`，它在列表的所有元素上应用`ok`，然后把结果全部按顺序收集起来，组成结果列表。

## 转译过程的实例

下面这个列表生成式计算所有$j \le i^2$的互素数对$(i, j)$：

{% highlight haskell %}
coprimes = [ (i, j) | i <- [1 ..]
                    , let k = i * i
                    , j <- [1 .. k]
                    , gcd i j == 1 ]
{% endhighlight %}

应用上述转译方案，它可以被翻译成如下使用普通函数的等价写法（具体过程留给读者作为习题:laughing:）：

{% highlight haskell %}
coprimes =
  let f i =
        let k = i * i in
        let g j = if gcd i j == 1
              then [ (i, j) ]
              else []
        in concatMap g [1 .. k]
  in concatMap f [1 ..]
{% endhighlight %}

当然，这不是这个问题的唯一翻译方法，我们完全可以把上面的代码略作改写得到：

{% highlight haskell %}
coprimes =
  concat $ [1 ..] <&> \i ->
    let k = i * i in
    catMaybes $ [1 .. k] <&> \j ->
      if gcd i j == 1
      then Just (i, j)
      else Nothing
{% endhighlight %}

第二种写法也许比直接翻译的第一种好，也许不好。第二种方法使用了`Data.Functor.(<&>)`、`Data.Maybe.catMaybes`，也许看上去更“高级”，也许不是。但可以确定的是，列表生成式的写法比这两种都要清晰明了。语法糖之所以存在，就是为了使代码变得清楚、简洁。一般而言，实际应用中很少需要把列表生成式翻译成普通形式，这种翻译的后果大多数情况下都是使代码可读性降低。
{:.warning}

不过，实际编码的过程中，确实存在一些情况有理由把列表生成式转译为普通形式。其中最常见的一种情况是，要做的事情已经有库函数可以做到了。例如：

```haskell
mapPlusOne lst = [ x + 1 | x <- lst ]
filterEven lst = [ x | x <- lst, even x ]
```

这可能就不如写成：

```haskell
mapPlusOne = map (+ 1)
filterEven = filter even
```

或者干脆就不要定义成一个单独的函数，直接用就好了。

## 列表Monad与列表生成式

### 列表Monad转译方案

很容易看出，列表生成式和列表Monad有很多相似之处。列表实现了`Monad`和`MonadPlus`（实际上只需要`Alternative`），我们完全可以利用`do`记号（do-notation）来转译列表生成式。具体的规则给出如下：

{% highlight haskell %}
[ e | True ]            = pure e
[ e | q ]               = [ e | q, True ]
[ e | b, Q ]            = do { guard b; [ e | Q ] }
[ e | p <- l, Q ]       = do { p <- l; [ e | Q ] }
[ e | let decls, Q ]    = do { let decls; [ e | Q ] }
{% endhighlight %}

由于AMP提案（functor-applicative-monad proposal）[(2)]，`Applicative`已经是`Monad`的超类（superclass），因此这里没有使用`return`，而是使用了`pure`。这纯粹是一个个人习惯。
{:.info}

这种方案和Haskell Report中给出的其实是等价的，只要考虑到`do`记号也是一个语法糖：

{% highlight haskell %}
do { p <- m; more }   = let f p = more
                            f _ = fail "..."
                        in m >>= f
do { m; more }        = m >>= \_ -> more
{% endhighlight %}

由于`MonadFail`提案[(3)]，这里的`fail`其实是`MonadFail`提供的（`Control.Monad.Fail.fail`），而不是`Monad`中的那个。不过这个事实在这里无关紧要，因为两个`fail`的定义都是空列表。
{:.info}

而对于列表，`(>>=) = flip concatMap`，`Control.Monad.guard`函数定义如下：

```haskell
guard :: Alternative f => Bool -> f ()
guard True  = pure ()
guard False = fail "..."
```

它在列表上特化为：

```haskell
guard :: Bool -> [()]
guard True  = [()]
guard False = []
```

因此实际上`do { guard b; m }`在列表上有如下翻译：

```haskell
  do { guard b; m }
= guard b >>= \_ -> m
= concatMap (\_ -> m) (if b then [()] else [])
= if b then concatMap (\_ -> m) [()] else concatMap (\_ -> m) []
= if b then m else []
```

### Monad生成式

实际上，上一节我们给出的转译规则完全适用于任何Monad，因此GHC给出了一个语法扩展：Monad生成式[(4)]。它会按照上一小节的规则来将生成式翻译成对应形式，适用于任何Monad。

开启这个扩展的指令是`{-# LANGUAGE MonadComprehensions #-}`。
{:.success}

一个细节是，GHC给出的翻译没有使用`pure`，而是使用了`return`。这一般而言不成问题，因为对于大多数Monad的实现来说`return = pure`。但是考虑到`RebindableSyntax`扩展[(5)]之后，这就成为了需要注意的一点，因为我们必须重新绑定`return`而不是`pure`。
{:.warning}

## 并行列表生成式

列表生成式更类似过程式语言的嵌套循环，它依次遍历所有列表，并生成所有组合。有的时候我们希望两个列表的遍历是同步的，这时我们可以使用生成器`(a, b) <- zip as bs`。同理，如果希望三个列表的遍历同步，我们使用`(a, b, c) <- zip3 as bs cs`，以此类推。但是这种写法并不美观，也不直接。

GHC提供了并行列表生成式[(6)]来解决这个问题：对于上面两个表达式，我们可以写作：

```haskell
[ e | (a, b) <- zip as bs ]       = [ e | a <- as | b <- bs ]
[ e | (a, b) <- zip3 as bs cs ]   = [ e | a <- as | b <- bs | c <- cs ]
```

它的一般转译规则如下：给定如下形式的并行列表生成式：

{% highlight haskell %}
[ e | p₁ <- e₁₁, p₂ <- e₁₂, ...
    | q₁ <- e₂₁, q₂ <- e₂₂, ...
    ...
]
{% endhighlight %}

会被转译成如下形式：

{% highlight haskell %}
[ e | ((p₁, p₂), (q₁, q₂), ...) <-
        zipN [(p₁, p₂) | p₁ <- e₁₁, p₂ <- e₁₂, ...]
             [(q₁, q₂) | q₁ <- e₂₁, q₂ <- e₂₂, ...]
             ...
]
{% endhighlight %}

其中`zipN`是对应分支个数的`zip`函数。

开启这个扩展的指令是`{-# LANGUAGE ParallelListComp #-}`。
{:.success}

## 参考文献

1. [Haskell 2010 Report](https://www.haskell.org/definition/haskell2010.pdf).
2. [AMP提案](https://wiki.haskell.org/Functor-Applicative-Monad_Proposal)
3. [`MonadFail`提案](https://wiki.haskell.org/MonadFail_Proposal).
4. [Monad生成式](https://downloads.haskell.org/ghc/latest/docs/html/users_guide/glasgow_exts.html#monad-comprehensions).
5. [`RebindableSyntax`扩展](https://downloads.haskell.org/ghc/latest/docs/html/users_guide/glasgow_exts.html#rebindable-syntax).
6. [并行列表生成式](https://downloads.haskell.org/ghc/latest/docs/html/users_guide/glasgow_exts.html#parallel-list-comprehensions).

[(1)]: #参考文献 "Haskell 2010 Report"
[(2)]: #参考文献 "MonadFail提案"
[(3)]: #参考文献 "AMP提案"
[(4)]: #参考文献 "Monad生成式"
[(5)]: #参考文献 "RebindableSyntax扩展"
[(6)]: #参考文献 "并行列表生成式"
