import logging
log = logging.getLogger("partition")

class PartitionError(Exception):
    pass

def columnset_to_string(colset):
    s = list(colset)
    s.sort()
    # Add one, cos we converted to zero base...
    return ', '.join([str(x+1) for x in s])

class AllPartitions(object):
    """The set of all partitions loaded from a configuration file"""
    def __init__(self):
        """A set of Partitions"""
        self.sequence = 0
        self.parts_by_name = {}
        self.parts_by_number = {}
        self.partitions = set()

        # All of the columns
        self.columns = []
        self.columnset = set()

        self.finalised = False

    def __str__(self):
        return "AllPartitions(%s)" % ", ".join([str(p) for p in self.partitions])

    def add_partition(self, p):
        """Check for overlap (= intersection)"""
        if self.finalised:
            log.error("Cannot add partitions after a Scheme has been created")
            raise PartitionError

        if p.name in self.parts_by_name:
            log.error("Attempt to add %s when that name already exists", p)
            raise PartitionError

        overlap = []
        for otherp in all_partitions:
            if p.columnset & otherp.columnset:
                overlap.append(str(otherp))
        if overlap:
            log.error("%s overlaps with previously defined "
                      "partitions: %s",
                      p, ", ".join(overlap))
            raise PartitionError

        # Assign the partition to this set
        p.partition_set = self

        # Make sure we can look up by name
        self.parts_by_name[p.name] = p
        self.parts_by_number[self.sequence] = p
        self.sequence += 1
        self.partitions.add(p)

        # Merge all the columns
        self.columns.extend(p.columns)
        self.columns.sort()
        self.columnset |= p.columnset

    def finalise(self):
        """Internal check -- just for gaps now
        
        This is called when the first scheme is created
        """
        # It is sorted -- so the last one is the biggest
        self.colmin = self.columns[0]
        self.colmax = self.columns[-1]
        self.fullset = set(range(self.colmin, self.colmax+1))
        leftout = self.fullset - self.columnset
        if leftout:
            # This does not raise an error, just a warning
            log.warn(
                "Columns in all partitions range from %s to %s, "
                "but these columns are missing: %s", 
                self.colmin+1, self.colmax+1,
                columnset_to_string(leftout))

        self.finalised = True

    # We can treat this like a bit like a dictionary
    def __iter__(self):
        return iter(self.partitions)

    def __len__(self):
        return len(self.partitions)

    def __getitem__(self, k):
        if type(k) is int:
            return self.parts_by_number[k]
        return self.parts_by_name[k]

    def __contains__(self, k):
        return k in self.parts_by_name

    def names(self):
        return self.parts_by_name.keys()

all_partitions = AllPartitions()

class Partition(object):
    """A set of columns from an alignment"""
    def __init__(self, name=None, *partlist):
        """A named partition

        """
        # if name is None:
            # name = str(all_partitions.sequence)
        self.name = name
        description = []

        # This will get set later, when they are added to PartitionSet
        self.partition_set = None

        # We now need to convert to column definitions. Note that these are
        # zero based, which is not how they are specified in the config. So we
        # must do some fiddling to make sure they are right. In addition, we
        # use range(...) which excludes the final column, whereas the
        # definitions assume inclusive...
        columns = []
        for p in partlist:

            # Make sure it is sensible
            if len(p) < 2 or len(p) > 3:
                log.error("The Partition '%s' should contain\
                          a list of start, a stop, and an optional step",
                          self.name)
                raise PartitionError
            if len(p) == 2:
                start, stop = p
                step = 1
            else:
                start, stop, step = p
            if start >= stop:
                log.error("Partition '%s' has beginning after end (%s > %s)",
                          name, start, stop)
                raise PartitionError

            # Actually, subtracting 1 deals with both issues...
            columns.extend(range(start-1, stop, step))
            description.append((start, stop, step))

        self.description = tuple(description)

        # Normalise it all
        columns.sort()
        columnset = set(columns)

        # If there was any overlap then these will differ...
        if len(columns) != len(columnset):
            log.error("Partition '%s' has internal overlap", name)
            raise PartitionError

        # Both of these are useful?
        self.columns = columns
        self.columnset = columnset

        all_partitions.add_partition(self)
        log.debug("Created %s", self)

    def __repr__(self):
        outlist = ", ".join(["%s-%s\\%s" % tuple(p) for p in self.description])
        return "Partition<%s: %s>" % (self.name, outlist)

    def __str__(self):
        outlist = ", ".join(["%s-%s\\%s" % tuple(p) for p in self.description])
        return "Partition(%s, %s)" % (self.name, outlist)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    p1 = Partition('one', (1, 10))
    p2 = Partition('two', (11, 20))

    print all_partitions[0]
    # ps = PartitionSet(p1, p2)

    # print ps