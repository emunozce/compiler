"""
    Python file that contains the function get_tokens(file: Path)
    that extracts tokens from a file and returns a list of tokens along
    with their errors and it's positions.
"""

import sys
from pathlib import Path
import re


class Token:
    def __init__(self, type, value, lineno, lexpos):
        self.type = type
        self.value = value
        self.lineno = lineno
        self.lexpos = lexpos

    def __repr__(self):
        return f"Token({self.type}, {self.value}, {self.lineno}, {self.lexpos})"


def get_lexical_analysis(file: Path):
    with open(file, "r", encoding="utf-8") as f:
        tokens = []
        errors = []
        is_block_comment = False
        is_block_starting = []
        identifier_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        reserved_words_pattern = re.compile(
            r"\b(if|else|do|while|switch|case|double|main|cin|cout|int|real|then|end|until)\b"
        )
        number_pattern = re.compile(r"\b\d+\b")
        symbol_pattern = re.compile(r"\(|\)|,|{|}|;")
        assignment_pattern = re.compile(r"=")
        logical_op_pattern = re.compile(r"\b(?:and|or)\b")
        aritmethic_op_pattern = re.compile(r"\+|-|\*|/|%|\^")
        relational_op_pattern = re.compile(r"<|>|!")

        for lineno, line in enumerate(f.readlines(), start=1):
            skip_col = 0
            for index_string, char in enumerate(line):
                lexpos = index_string + 1
                if skip_col == 0:
                    if char == " ":
                        continue
                    if char == "\t":
                        continue
                    if char == "\n":
                        continue

                    if re.match(symbol_pattern, char) and not is_block_comment:
                        tokens.append(Token("SYMBOL", char, lineno, lexpos))
                        continue

                    if re.match(assignment_pattern, char) and not is_block_comment:
                        if (index_string + 1 < len(line)) and line[
                            index_string + 1
                        ] == "=":
                            tokens.append(Token("EQ", "==", lineno, lexpos))
                            skip_col += 1
                            continue
                        tokens.append(Token("ASSIGN", char, lineno, lexpos))
                        continue

                    if re.match(aritmethic_op_pattern, char) and not is_block_comment:
                        if char == "+" and line[index_string + 1] == "+":
                            tokens.append(
                                Token("INCREMENT_OPERATOR", "++", lineno, lexpos)
                            )
                            skip_col += 1
                            continue
                        if char == "-" and line[index_string + 1] == "-":
                            tokens.append(
                                Token("DECREMENT_OPERATOR", "--", lineno, lexpos)
                            )
                            skip_col += 1
                            continue
                        if (
                            char == "/"
                            and (index_string + 1 < len(line))
                            and (line[index_string + 1] == "*")
                        ):
                            is_block_starting = [lineno, lexpos]
                            is_block_comment = True
                            break
                        if (
                            char == "/"
                            and (index_string + 1 < len(line))
                            and line[index_string + 1] == "/"
                        ):
                            break
                        tokens.append(
                            Token("ARITHMETIC_OPERATOR", char, lineno, lexpos)
                        )
                        continue

                    if re.match(relational_op_pattern, char) and not is_block_comment:
                        if (index_string + 1 < len(line)) and line[
                            index_string + 1
                        ] == "=":
                            tokens.append(
                                Token("RELATIONAL_OPERATOR", char + "=", lineno, lexpos)
                            )
                            skip_col += 1
                            continue
                        tokens.append(
                            Token("RELATIONAL_OPERATOR", char, lineno, lexpos)
                        )
                        continue

                    if re.match(identifier_pattern, char) and not is_block_comment:
                        identifier = char
                        rest_of_string = line[index_string + 1 :]
                        while True:
                            for c in rest_of_string:
                                if re.match(identifier_pattern, c):
                                    identifier += c
                                    skip_col += 1
                                else:
                                    break
                            break

                        if re.match(logical_op_pattern, identifier):
                            tokens.append(
                                Token("LOGICAL_OPERATOR", identifier, lineno, lexpos)
                            )
                            continue

                        if re.match(reserved_words_pattern, identifier):
                            tokens.append(
                                Token("RESERVED_WORD", identifier, lineno, lexpos)
                            )
                            continue

                        tokens.append(Token("IDENTIFIER", identifier, lineno, lexpos))
                        continue

                    if re.match(number_pattern, char) and not is_block_comment:
                        number = char
                        rest_of_string = line[index_string + 1 :]
                        is_float_recognized = False
                        while True:
                            for i_c, c in enumerate(rest_of_string):
                                if re.match(number_pattern, c):
                                    number += c
                                    skip_col += 1
                                elif (
                                    c == "."
                                    and re.match(
                                        number_pattern, rest_of_string[i_c + 1]
                                    )
                                    and not is_float_recognized
                                ):
                                    is_float_recognized = True
                                    number += c
                                    skip_col += 1
                                else:
                                    break
                            break
                        if is_float_recognized:
                            if (
                                tokens
                                and tokens[-1].type == "ARITHMETIC_OPERATOR"
                                and tokens[-1].value == "-"
                            ):
                                tokens.pop()
                                number = "-" + number
                            tokens.append(Token("REAL_NUMBER", number, lineno, lexpos))
                            continue
                        if (
                            tokens
                            and tokens[-1].type == "ARITHMETIC_OPERATOR"
                            and tokens[-1].value == "-"
                        ):
                            tokens.pop()
                            number = "-" + number
                        tokens.append(Token("INTEGER_NUMBER", number, lineno, lexpos))
                        continue

                    if not is_block_comment:
                        errors.append(
                            {
                                "Error": char,
                                "Ln": lineno,
                                "Col": lexpos,
                            }
                        )

                    if is_block_comment:
                        if (
                            char == "*"
                            and (index_string + 1 < len(line))
                            and line[index_string + 1] == "/"
                        ):
                            is_block_comment = False
                            skip_col += 1
                else:
                    skip_col -= 1

        if is_block_comment:
            errors.append(
                {
                    "Error": f"Block comment not closed at Ln: {is_block_starting[0]}, Col {is_block_starting[1]}"
                }
            )

        return tokens, errors


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        print("No arguments provided")
    elif len(args) > 2:
        print("Bad arguments")
    else:
        file_path = Path(args[1])
        if not file_path.exists():
            print("File does not exist")
        else:
            # bytes = file_path.read_bytes()
            # print(bytes)
            tkns, errs = get_lexical_analysis(file_path)

            for token in tkns:
                print(f"{token}")

            for error in errs:
                print(f"{error}")
