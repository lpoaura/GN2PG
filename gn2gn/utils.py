class BColors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


transtable = str.maketrans(
    "àâäéèêëîïôöùûüŷÿç~- ",
    "aaaeeeeiioouuuyyc___",
    "&'([{|}])`^\/+-=*°$£%§.?!;:<>",
)


def simplify(source):
    """[summary]

    Args:
        source ([type]): [description]

    Returns:
        [type]: [description]
    """
    clean_result = " ".join(source.split())
    newsource = clean_result.lower().translate(transtable)
    return newsource
