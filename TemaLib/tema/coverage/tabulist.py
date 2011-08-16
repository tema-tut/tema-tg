
""" TabuList.
    Separate implementations for LimitedTabuList and UnlimitedTabuList.
"""

class TabuList(object):
    """ TabuList contains some items, added with the add() method.
        TabuList can be pushed and popped. A pop restores the tabulist to
        the state it was before the corresponding push.

        TabuList interface:
            add(item)
            __contains__(item)
            __len__()
            __iter__()
            push()
            pop()

        tl = TabuList()
        tl.add(7)
        tl.add(8)
        tl.add(8)
        # len(tl) == 2, contains: 7,8
        tl.push()
        tl.add(10)
        tl.add(11)
        # len(tl) == 4, contains: 7,8,10,11
        tl.pop()
        # len(tl) == 2, contains: 7,8
    """

    def __new__(cls, max_size=None):
        """ Returns a TabuList.
            max_size is a natural number -> LimitedTabuList(max_size)
            max_size is anything else (or omitted) -> UnlimitedTabuList()
        """
        try:
            max_size = int(max_size)
        except:
            max_size = None

        if max_size is None or max_size < 0:
            return super(TabuList,cls).__new__(UnlimitedTabuList)
        else:
            return super(TabuList,cls).__new__(LimitedTabuList)


# a separate implementation for unlimited tabulist cause it's much simpler
# and a bit faster (for the same size) than the limited one.
class UnlimitedTabuList(TabuList):
    """ UnlimitedTabuList contains an unlimited number of items.
        Once an item is added, it will never be removed.
        Unlimited tabulist can be pushed/popped, though.
        A pop restores the tabulist to the state it was before
        the corresponding push.
    """
    # there must be an (unused) parameter cause the superclass has one too (?)
    def __init__(self,max_size=None):
        self.clear()

    def clear(self):
        # _setStack[N] contains the items added on the Nth pushlevel.
        self._setStack = [ set() ]
        # _lenStack[N] is the number of items that have been added
        # on the Nth pushlevel. the current size is always sum(_lenStack).
        self._lenStack = [0]
        # all the current items in one set for faster searching.
        self._currItems = set()

        self._pushLevel = 0

    def add(self,item):
        if item not in self._currItems:
            self._setStack[-1].add(item)
            self._currItems.add(item)
        # the size increases even if we already had the item
        self._lenStack[-1] += 1

    def __contains__(self,item):
        return item in self._currItems

    def __len__(self):
        return len(self._currItems)
    lenUnique = __len__

    #def lenInclDuplicates(self):
    #    return sum(self._lenStack)

    def push(self):
        self._pushLevel += 1
        self._setStack.append( set() )
        self._lenStack.append(0)

    def pop(self):
        self._pushLevel -= 1
        self._lenStack.pop()
        popped = self._setStack.pop()
        self._currItems.difference_update(popped)

    def __iter__(self):
        return self._currItems.__iter__()

    def __str__(self):
        return "{%s}" % ", ".join([str(item) for item in self])


class LimitedTabuList(TabuList):
    """ LimitedTabuList contains maximum of 'max_size' items.
        There may be multiple equal items.
        If the Tabulist is full (= contains max_size items) and a new item is
        added, the oldest item of the list is removed.
        May be pushed and popped. A pop restores the tabulist to the state
        it was before the corresponding push.

        tl = TabuList(2)
        tl.add(7)
        # len(tl) == 1, tl.lenInclDuplicates() == 1, contains: 7
        tl.add(8)
        tl.add(8)
        # len(tl) == 1, tl.lenInclDuplicates() == 2, contains: 8
        tl.push()
        tl.add(10)
        # len(tl) == 2, tl.lenInclDuplicates() == 2, contains: 8,10
        tl.pop()
        # len(tl) == 1, tl.lenInclDuplicates() == 2, contains: 8
    """

    def __init__(self,max_size):
        """Creates an empty Tabulist of the given maximum size.
        """
        self.MAX_SIZE = max_size
        self.clear()

    def clear(self):
        self._size = 0

        self._pushLevel = 0

        # _listStack[N] contains the items added on the Nth push level.
        # the size of a list grows until its len is MAX_SIZE. then it
        # acts like a ring buffer where _posStack[N] tells the position of
        # the oldest item in the list.
        self._listStack = [ [] ]
        self._posStack = [ 0 ]

        # when adding something while pushed, we may need to remove something
        # from lower pushlevels to keep the size of the tabulist as MAX_SIZE.
        # we don't actually remove items, we'll just mark them removed and
        # bring them back when the removal-causing pushlevel has been popped.
        # _removedByHigher[X][Y-X-1] says how many removals pushlevel Y has
        # caused at a lower pushlevel X.
        # a total of sum(_removedByHigher[X]) items have been removed
        # from level X by all its higher pushlevels.
        self._removedByHigher = [ [] ]
        
        # _currItems contains all the current items, for faster searching.
        # key: item, value: how many of those items there are
        self._currItems = {}

    def add(self,item):
        if self.MAX_SIZE == 0:
            return

        addLevel = self._pushLevel

        # if full, remove the oldest item
        if self._size == self.MAX_SIZE:
            # remove from the lowest pushlevel that has some items
            for remLevel,li in enumerate(self._listStack):
                remByHi = sum(self._removedByHigher[remLevel])
                if remByHi < len(li):
                    break

            # remove the oldest item that hasn't been removed yet.
            # it's at oldestNRPos.
            oldestNRPos = (self._posStack[remLevel] + remByHi) % self.MAX_SIZE
            oldest = self._listStack[remLevel][oldestNRPos]
            if remLevel == addLevel:
                # all the (MAX_SIZE) items are on the same (highest) pushlevel.
                # overwriting the oldest item.
                self._listStack[addLevel][oldestNRPos] = item
                self._posStack[addLevel] = (oldestNRPos+1) % self.MAX_SIZE
            else:
                # appending an item on the highest pushlevel
                # and removing an item from a lower pushlevel.
                self._listStack[addLevel].append(item)
                self._removedByHigher[remLevel][addLevel-remLevel-1] += 1
            # remove from _currItems, too.
            self._currItems[oldest] -= 1
            if self._currItems[oldest] == 0:
                del self._currItems[oldest]
        else:
            # tabulist not full yet, simply appending
            self._listStack[addLevel].append(item)
            self._size += 1
        # add to _currItems, too.
        if self._currItems.has_key(item):
            self._currItems[item] += 1
        else:
            self._currItems[item] = 1

    def __contains__(self,item):
        return item in self._currItems

    def __len__(self):
        return len(self._currItems)
    lenUnique = __len__

    def lenInclDuplicates(self):
        return self._size

    def push(self):
        self._pushLevel += 1
        if self.MAX_SIZE == 0:
            return
        self._listStack.append( [] )
        self._posStack.append( 0 )
        for rb in self._removedByHigher:
            rb.append( 0 )
        self._removedByHigher.append( [] )

    def pop(self):
        self._pushLevel -= 1
        if self.MAX_SIZE == 0:
            return
        if self._pushLevel < 0:
            raise ValueError("Can't pop a non-pushed TabuList!")
        poppedList = self._listStack.pop()
        self._posStack.pop()
        self._removedByHigher.pop()

        numPopped = 0
        # remove the popped items from _currItems
        for x in poppedList:
            numPopped += 1
            self._currItems[x] -= 1
            if self._currItems[x] == 0:
                del self._currItems[x]

        numRemovedByPopped = 0
        # restore the items that have been removed by the popped level
        for i,rb in enumerate(self._removedByHigher):
            # nrPos = pos of the newest removed item.
            # restore numRemovedByPoppedFromThis items left from there.
            nrPos = (self._posStack[i] + sum(self._removedByHigher[i]) - 1)\
                    % self.MAX_SIZE
            numRemovedByPoppedFromThis = rb.pop()
            for k in xrange(numRemovedByPoppedFromThis):
                item = self._listStack[i][nrPos]
                if self._currItems.has_key(item):
                    self._currItems[item] += 1
                else:
                    self._currItems[item] = 1
                nrPos = (nrPos-1) % self.MAX_SIZE
            numRemovedByPopped += numRemovedByPoppedFromThis

        self._size -= ( numPopped - numRemovedByPopped )

    def __iter__(self):
        return self._currItems.__iter__()
    iterUnique = __iter__

    def iterInclDuplicates(self):
        """Yields all the items from oldest to newest."""
        # yield all the non-removed items starting from the lowest pushlevel.
        for i,li in enumerate(self._listStack):
            removed = sum(self._removedByHigher[i])
            le = len(li)
            if le > removed:
                # there are non-removed items in the list
                pos = self._posStack[i]
                k = (pos+removed) % le # start from the oldest non-removed
                while True:
                    yield li[k]
                    k = (k+1) % le
                    if k == pos:
                        break

    def __str__(self):
        return "[%s]" % ", ".join([str(item) for item in self])

