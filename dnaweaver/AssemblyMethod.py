from dnachisel.biotools import reverse_complement

class AssemblyMethod:
    """General class for assembly methods.

    Yeah that class is useless right now but bear with me.
    """
    name = "None"
    def __init__(self, duration=0, cost=0, location_filters=(),
                 segment_filters=(), min_segment_length=None,
                 max_segment_length=None, force_cuts=(),
                 sequence_constraints=(), name=None):
        self.duration = duration
        self.cost = cost
        self.location_filters = location_filters
        self.segment_filters = segment_filters
        self.min_segment_length = min_segment_length
        self.max_segment_length = max_segment_length
        self.sequence_constraints = sequence_constraints
        if callable(force_cuts):
            self.force_cuts = force_cuts
        else:
            self.force_cuts = lambda *a: force_cuts


class OverlapingAssemblyMethod(AssemblyMethod):
    """Gibson Assembly Method.

    Parameters
    ----------

    homology_arm_length
      Length of the homology arm, or "overhang". A length of L means that
      consecutive segments will overlap by 2*L

    """
    name= "Overlap"

    def __init__(self, homology_arm_length=20, **properties):
        AssemblyMethod.__init__(self, **properties)
        self.homology_arm_length = homology_arm_length




    def compute_fragment_sequence(self, sequence, segment):
        """Return the segment's sequence with flanking sequences.

        Parameters
        ----------

        segment
          A pair of integers (start, end) delimiting the subfragment
          sequence[start:stop]

        sequence
          An "ATGC" DNA sequence string

        """
        L = len(sequence)
        start, end = segment
        return sequence[max(0, start - self.homology_arm_length):
                        min(L, end + self.homology_arm_length)]

class GibsonAssemblyMethod(OverlapingAssemblyMethod):
    """Gibson Assembly Method. Just another overlap-method"""
    name = "Gibson"

class BuildAGenomeAssemblyMethod(OverlapingAssemblyMethod):
    """The Build-a-Genome Assembly Method. Just another overlap-method"""
    name = "BaG"

class GoldenGateAssemblyMethod(AssemblyMethod):
    """The Golden Gate Assembly Method.

    This method adds overhangs with a Type IIS REase site to the segments.

    Parameters
    ----------

    left_overhang
      An ATGC DNA sequence representing the left overhang, in 5' -3'.
      For practicality, this can contain "[BsaI]", "[BsmBI]", "[BbsI]", which
      will be replaced by their restriction sites


    right_overhang
      An ATGC DNA sequence representing the right overhang, in 5'-3'.
      Be careful, I said 5'-3' !!!
      If left to None, will be equal to left_overhang.

    Examples
    --------

    >>> #  The fragments will have an overhang with an homology region, a BsaI
    >>> #  site, and a "T" for the wildcard
    >>> assembly_method = GoldenGateAssemblyMethod(
    >>>  left_overhang = "ATGTGTCGTGTGTGCGTA[BsaI]T",
    >>>  right_overhang = "TTCTCTCGATAAATGGCC[BsaI]T"
    >>> )

    """
    name = "Golden Gate"

    enzymes_dict = {
        "BsaI": "GGTCTC",
        "BsmBI": "CGTCTC",
        "BbsI": "GAAGAC",
    }

    def __init__(self, enzyme="BsaI", wildcard_basepair="A",  left_overhang="",
                 right_overhang="", avoid_enzyme_in_segments=False,
                 **properties):
        AssemblyMethod.__init__(self, **properties)
        self.enzyme = enzyme
        enzyme_site = self.enzymes_dict[enzyme]
        enzyme_site_plus_basepair = enzyme_site + wildcard_basepair
        self.left_overhang = left_overhang + enzyme_site_plus_basepair
        self.right_overhang = right_overhang + enzyme_site_plus_basepair
        self.right_overhang_rev = reverse_complement(self.right_overhang)
        if avoid_enzyme_in_segments:
            self.segment_filters = list(self.segment_filters) + [
                lambda seq, start, end: (enzyme_site not in seq[start:end])
            ]

    def compute_fragment_sequence(self, sequence, segment):
        """Return the segment's sequence with flanking sequences for

        Parameters
        ----------

        segment
          A pair of integers (start, end) delimiting the subfragment
          sequence[start:stop]

        sequence
          An "ATGC" DNA sequence string

        """
        L = len(sequence)
        start, end = segment
        segment = sequence[max(0, start - 2): min(L, end + 2)]
        return self.left_overhang + segment + self.right_overhang_rev