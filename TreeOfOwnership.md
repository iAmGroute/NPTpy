
# This document describes the Tree Of Ownership (.too) code description format.

## What is it ?
The TOO shows an ownership diagram: a graph where each node/vertex represents an object and each link/edge shows that one object is owned by the other.
An ownership diagram is directed, with the links starting from a parent object and pointing to the objects that it owns.
The TOO specifically assumes that the object graph is (almost) a tree and has a single root.

## Representation

### A simple tree

First, let's assume the following code:
```python
class A:
    def __init__(self):
        self.b = B()
        self.c = C()

class B:
    def __init__(self):
        self.url  = 'example.com'
        self.path = '/index.html'

class C:
    def __init__(self):
        self.counter = 5

a = A()
while True:
    pass
```
When executed, 6 objects (that we are interested in) are created:
* `a` of type `A`, which has (owns) 2 other objects:
    * `a.b` of type `B`, which has 2 other objects:
        * `a.b.url` of type `str` and
        * `a.b.path` of type `str`
    * `a.c` of type `C`, which has 1 other object:
        * `a.c.counter` of type `int`
This object graph is a tree with `a` as its root.

In the TOO format it would be respresented as:
```makefile
a               = A
    b           = B
        url     = str
        path    = str
    c           = C
        counter = int
```
As you can see, the object's name is added on the left, then spaces the `=` followed by 1 space, then the object's type.
The objects that are owned by an object, are idented using 4 spaces.

However, usually, we do not care about trivial objects and so omit them from the TOO.
Which objects are considered trivial depends on the application, in this case, we could consider primitive types to be trivial.
Furthermore, we can make it obvious that `a` is the root of the TOO by naming it as such (`root`).
Our updated TOO would look like this:
```makefile
root  = A
    b = B
    c = C
```
A lot of information is omitted and only the backbone of our application is shown in order to make it possible to depict significantly larger ownership graphs (and thus be used to describe more complex code bases).

### A tree that is not technically a tree: trees with back-edges

Sometimes, objects have a reference to their parent/owner.

#### Let's examine this code:
```python
class A:
    def __init__(self):
        self.b = B()
        self.c = C(self, 5)
        self.d = D('world')

class B:
    def __init__(self):
        self.url  = 'example.com'
        self.path = '/index.html'

class C:
    def __init__(self, parent, counter):
        self.parent  = parent
        self.counter = counter

class D:
    def __init__(self, hello):
        self.hello = hello

a = A()
while True:
    pass
```
If we assume that having a reference to an object is the same as owning it, the above code results in an ownership graph that has a cycle:
`a` owns `a.b` and `a.b` owns `a`
**or** one could say:
`b` owns `b.parent` and `b.parent` owns `b`
Programmatically, it makes no difference as a result of *owning* being the same as *having a referece to*.
(In some other languages, like Rust, the concept of ownership is stricter and the above doesn't apply.)
However, when looking at the code as humans, we see a (clear) distinction: `a` owns `a.b` and not the other way around.
This could mean a few things, such as:
* there is a problem with the code, a bug, an issue waiting to happend, perhaps a memory leak
* the parent reference should actually be a weak reference (see [weakref](https://docs.python.org/3/library/weakref.html))
* the code is fine, but we need to be aware of this reference cycle and deal with it
There are cases where the cycle can be removed, but there are also some where it is there intentionally.
In the format we are describing, we will chose to allow these back-references and depict them in a prominent way:
```makefile
root  = A
 |  b = B
 '- c = C
    d = D
```
We use the `|`, `'` and `-` characters to mark a line that begins from the object that contains the back-edge (here it's `c`) and ends at the object it is referencing (here it's `root` or `a`).
There is 1 space between the last `-` and the name of the object and the vetrical line is idented by 1 space from the level of the referenced object.
Note that the line starts from the name of the object that *contains* the refernce (`c`), not the name of the reference (`parent`, which is not shown in the TOO).
Also note that weak references are not depicted at all.

#### A more extensive example:
```python
class A:
    def __init__(self):
        self.b      = B(self)
        self.things = []
        self.d      = D('world')
    def addThing(self, counter):
        self.things.append(Thing(self, counter))
    def greet(self, number):
        g = self.d.getGreeting()
        print(f'{g}, the number is {number}')

class B:
    def __init__(self, parent):
        self.parent = parent
        self.url    = 'example.com'
        self.path   = '/index.html'

class Thing:
    def __init__(self, parent, counter):
        self.parent = parent
        self.c      = C(counter)
    def greet(self):
        self.parent.greet(self.c.counter)

class C:
    def __init__(self, counter):
        self.counter = counter

class D:
    def __init__(self, hello):
        self.hello = hello
    def getGreeting(self):
        return 'Hello ' + self.hello

a = A()
while True:
    pass
```
```makefile
root          = A
 |- b         = B
 |  things    = list
 '----- item  = Thing
            c = C
    d         = D
```
*For a more complete and realistic example, see [Portal.too](./NPTpy/Portal/Portal.too)*
*The term `item` is used for an item inside a list (for no reason other than it seems ok :smiley:)*

#### teardown()
Noting these back-edges is important, as it can lead to memory leaks, and worse, objects staying alive when we think they've been deleted,
if the objects in the cycle override the `__del__` method.
In this repository, we make the agreement that every object that has incident back-edges (== back-references that point **to** it) must have a `teardown()` method, in which it is responsible for calling the `teardown()` method to all its descendants that also have incident back-edges and deleting its forth-edges (== forward/normal references it has to the objects it owns). An example from [Portal.py](./NPTpy/Portal/Portal.py):
```python
    def teardown(self):
        for link in self.links:
            link.teardown()
        self.links    = None
        self.connect  = None
        self.promises = None
```

## Extensions

### Module delegates

Module delegates are objects that are created by (usually) top-level modules and are owned by regular objects.
The delegates can have references to their modules which are usually outside the TOO.
Any reference **to** delegates must be a weak reference, except for the reference that the host object holds to it.
Delegates are shown in the `.too` files with a `%` in front of their class name.
More on this topic in another document *(aka TODO)*.

### Interfaces

Since we already have a nice layout of the object graph in the `.too` file, it is very convenient to add the interface between the TOO's objects here as well.
At this point, the interface only mentions the methods of one object that are called by another.
For the above 'extensive example' we have:
```makefile
# A

A     ---> B b:
    pass
A     <--- B b:
    pass

A     ---> Thing things.item:
    pass
A     <--- Thing things.item:
    greet(self, number)

A     ---> D d:
    getGreeting(self)

# Thing

Thing ---> C c:
    counter
```
A few things to note here:
* On the left, we have class names, then an arrow, then a class name and also the object's name.
* The object on the right is owned by the object of the class on the left.
* `pass` means there isn't anything there (empty line).
* When there is a back-edge, there must be a corresponding line with the `<---` arrow, even if it's just `pass`.
* The `--->` and `<---` lines that are otherwise identical have no empty line between their blocks, all other blocks are separated by an empty line.
* The blocks that refer to the same class (on the left) are grouped together with a nice header comment on top with the class's name (`# A`). This comment has 1 empty line on top and 1 on the bottom. There is no compiler to complain about this but people might :cop:.
* If the link/edge that the arrow represents is a weak reference, a `?` is used in place of the last `-`, like this:
    ```makefile
    A     ---> Something s:
        pass
    A     <--? Something s:
        doStuff(self)
    ```
* There could be many instances of the same object under different classes:
    ```makefile
    A     ---> Something s:
        pass
    A     ---> BetterSomething s:
        pass
    A     ---> EvenBetterSomething s:
        pass
    ```
* The method declarations are to be copied from source with only those optional arguements that are used in the actual calls (with the default values removed, if any). A function without `self` as its first arguement will be considered a class function (and colorized differently), not an object method!
* Keywords like `async` may be added after the `:` and a lot of spaces :wink:.
* Sometimes you can use `*` together with letters like a glob to refer to many similar functions.

## This is still not set in stone, many things may be changed or added in the future :no_mouth:.

*(BTW, everything noted here is totally informal and may in some cases contradict 'real' theory. This format and ideas on interpretation of any piece of code are meant only for the contributors of this particular repository and might not apply that well in other cases.)*

