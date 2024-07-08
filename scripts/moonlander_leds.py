layout = """
0 5 10 15 20 25 29         65 61 56 51 46 41 36
1 6 11 16 21 26 30         66 62 57 52 47 42 37
2 7 12 17 22 27 31         67 63 58 53 48 43 38
3 8 13 18 23 28               64 59 54 49 44 39
4 9 14 19 24    35         71    60 55 50 45 40
             32 33 34   70 69 68
"""


layout_indices = []
for row in layout.split("\n"):
    for col in row.split():
        col = col.strip()
        if not col:
            continue
        layout_indices.append(f"l{col}")


print(
    """
# define LED_LAYOUT({indices})\\
    {indices_ordered}

# define LED_LAYOUT_ALL(color) \\
    LED_LAYOUT({each_color})

""".format(
        indices=", ".join(layout_indices),
        indices_ordered=", ".join(f"l{i}" for i in range(len(layout_indices))),
        each_color=",".join(["(color)"] * len(layout_indices)),
    )
)
