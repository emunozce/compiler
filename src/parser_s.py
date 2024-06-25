from lexer import Token
from anytree import NodeMixin, RenderTree


class Node(NodeMixin):
    def __init__(self, name, value=None, children=None):
        self.name = name
        self.value = value
        if children:
            self.children = children

    def __str__(self):
        if self.value:
            return f"{self.value}"
        else:
            return f"{self.name}"


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.tokens[self.current_token_index]
        self.errors = []  # Añadir una lista para almacenar errores

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token_index += 1
            if self.current_token_index < len(self.tokens):
                self.current_token = self.tokens[self.current_token_index]
        else:
            error_message = f"Unexpected token {self.current_token.type}, expected {token_type} at line {self.current_token.lineno}, position {self.current_token.lexpos}"
            self.errors.append(error_message)
            self.synchronize()

    def synchronize(self):
        # Saltar tokens hasta encontrar uno que pueda comenzar una nueva declaración
        while self.current_token_index < len(self.tokens) and self.current_token.type not in ["SEMICOLON", "RBRACE", "LBRACE"]:
            self.current_token_index += 1
            if self.current_token_index < len(self.tokens):
                self.current_token = self.tokens[self.current_token_index]

        # Saltar el token de sincronización
        if self.current_token_index < len(self.tokens):
            self.current_token_index += 1
            if self.current_token_index < len(self.tokens):
                self.current_token = self.tokens[self.current_token_index]

    def parse(self):
        program_node = self.program()
        if self.errors:
            error_node = Node(name="Errors", children=[Node(name="Error", value=error) for error in self.errors])
            program_node.children = program_node.children + (error_node,)
        return program_node

    def program(self):
        token = self.current_token
        self.eat("MAIN")
        self.eat("LBRACE")
        declarations = self.declaration_list()
        statements = self.sentence_list()
        self.eat("RBRACE")
        return Node(
            name="Program",
            value=token.value,
            children=declarations + statements,
        )

    def declaration_list(self):
        declarations = []
        while self.current_token and self.current_token.type in [
            "INT",
            "DOUBLE",
            "FLOAT",
        ]:
            declarations.append(self.declaration_statement())
        return declarations

    def declaration_statement(self):
        if self.current_token.type == "INT":
            return self.variable_declaration("int")
        elif self.current_token.type == "DOUBLE":
            return self.variable_declaration("double")
        elif self.current_token.type == "FLOAT":
            return self.variable_declaration("float")
        else:
            return self.sentence()

    def variable_declaration(self, type):
        self.eat(type.upper())
        ids = self.identifier()
        self.eat("SEMICOLON")
        return Node(name="VariableDeclaration", value=type, children=ids)

    def identifier(self):
        ids = []
        ids.append(self.current_token.value)
        self.eat("IDENTIFIER")
        while self.current_token and self.current_token.type == "COMMA":
            self.eat("COMMA")
            ids.append(self.current_token.value)
            self.eat("IDENTIFIER")
        return [Node(name="Identifier", value=id) for id in ids]

    def sentence_list(self):
        statements = []
        while self.current_token and self.current_token.type != "RBRACE":
            try:
                statements.append(self.sentence())
            except Exception as e:
                self.errors.append(str(e))
                self.synchronize()
        return statements

    def sentence(self):
        if self.current_token.type == "IF":
            return self.if_statement()
        elif self.current_token.type == "WHILE":
            return self.while_loop_sentence()
        elif self.current_token.type == "DO":
            return self.do_while_loop_sentence()
        elif self.current_token.type == "CIN":
            return self.cin_sentence()
        elif self.current_token.type == "COUT":
            return self.cout_sentence()
        elif self.current_token.type == "IDENTIFIER":
            return self.assignment_or_increment_decrement()
        else:
            raise Exception(f"Unexpected token {self.current_token.type}")

    def assignment_or_increment_decrement(self):
        identifier_token = self.current_token.value
        self.eat("IDENTIFIER")

        if self.current_token.type == "ASSIGN":
            assign_token = self.current_token
            self.eat("ASSIGN")
            expression = self.sent_expression()
            self.eat("SEMICOLON")
            return Node(
                "Assignment",
                value=assign_token.value,
                children=[Node("Identifier", value=identifier_token), expression],
            )
        elif self.current_token.type == "INCREMENT_OPERATOR":
            operator_token = self.current_token
            self.eat("INCREMENT_OPERATOR")
            self.eat("SEMICOLON")
            return Node(
                name="Increment",
                value=operator_token.value,
                children=[Node(name="Identifier", value=identifier_token)],
            )
        elif self.current_token.type == "DECREMENT_OPERATOR":
            operator_token = self.current_token
            self.eat("DECREMENT_OPERATOR")
            self.eat("SEMICOLON")
            return Node(
                name="Decrement",
                value=operator_token.value,
                children=[Node("Identifier", value=identifier_token)],
            )
        else:
            raise Exception(f"Unexpected token {self.current_token.type}")

    def assignment(self):
        identifier_token = self.current_token.value
        self.eat("IDENTIFIER")
        assign_token = self.current_token
        self.eat("ASSIGN")
        expression = self.sent_expression()
        self.eat("SEMICOLON")
        return Node(
            name="Assignment",
            value=assign_token.value,
            children=[Node(name="Identifier", value=identifier_token), expression],
        )

    def sent_expression(self):
        if self.current_token.type == "SEMICOLON":
            self.eat("SEMICOLON")
            return Node("EmptyStatement")
        else:
            return self.expression()

    def if_statement(self):
        self.eat("IF")
        self.eat("LPAREN")
        condition = self.expression()
        self.eat("RPAREN")
        self.eat("LBRACE")
        true_branch = self.sentence_list()
        self.eat("RBRACE")

        if self.current_token and self.current_token.type == "ELSE":
            self.eat("ELSE")
            self.eat("LBRACE")
            false_branch = self.sentence_list()
            self.eat("RBRACE")
            return Node(
                name="If",
                value="if",
                children=[
                    condition,
                    Node(name="TrueBranch", value="true_branch", children=true_branch),
                    Node(
                        name="FalseBranch", value="false_branch", children=false_branch
                    ),
                ],
            )
        else:
            return Node(
                name="If",
                value="if",
                children=[
                    condition,
                    Node(name="TrueBranch", value="true_branch", children=true_branch),
                ],
            )

    def while_loop_sentence(self):
        self.eat("WHILE")
        self.eat("LPAREN")
        condition = self.expression()
        self.eat("RPAREN")
        self.eat("LBRACE")
        statements = self.sentence_list()
        self.eat("RBRACE")
        return Node(name="While", value="while", children=[condition] + statements)

    def do_while_loop_sentence(self):
        self.eat("DO")
        self.eat("LBRACE")
        statements = self.sentence_list()
        self.eat("RBRACE")
        self.eat("WHILE")
        self.eat("LPAREN")
        condition = self.expression()
        self.eat("RPAREN")
        return Node(name="DoWhile", value="do_while", children=statements + [condition])

    def cin_sentence(self):
        identifier = self.current_token.value
        self.eat("CIN")
        self.eat("IDENTIFIER")
        self.eat("SEMICOLON")
        return Node(name="Input", value=identifier)

    def cout_sentence(self):
        identifier = self.current_token.value
        self.eat("COUT")
        expression = self.expression()
        self.eat("SEMICOLON")
        return Node(name="Output", value=identifier, children=[expression])

    def expression(self):
        node = self.logical_expression()
        if self.current_token and self.current_token.type in [
            "LT",
            "LE",
            "GT",
            "GE",
            "EQ",
            "NE",
        ]:
            token = self.current_token
            self.eat(token.type)
            node = Node(
                name=token.type,
                value=token.value,
                children=[node, self.logical_expression()],
            )
        return node

    def logical_expression(self):
        node = self.simple_expression()
        while self.current_token and self.current_token.type in ["AND", "OR"]:
            token = self.current_token
            self.eat(token.type)
            node = Node(
                name=token.type,
                value=token.value,
                children=[node, self.simple_expression()],
            )
        return node

    def simple_expression(self):
        node = self.term()
        while self.current_token and self.current_token.type in ["PLUS", "MINUS"]:
            token = self.current_token
            self.eat(token.type)
            node = Node(
                name=token.type, value=token.value, children=[node, self.term()]
            )
        return node

    def term(self):
        node = self.factor()
        while self.current_token and self.current_token.type in [
            "TIMES",
            "DIVIDE",
            "MOD",
        ]:
            token = self.current_token
            self.eat(token.type)
            node = Node(
                name=token.type, value=token.value, children=[node, self.factor()]
            )
        return node

    def factor(self):
        node = self.component()
        while self.current_token and self.current_token.type == "POW":
            token = self.current_token
            self.eat("POW")
            node = Node(
                name=token.type, value=token.value, children=[node, self.component()]
            )
        return node

    def component(self):
        if self.current_token.type == "LPAREN":
            self.eat("LPAREN")
            node = self.expression()
            self.eat("RPAREN")
            return node
        elif self.current_token.type in [
            "INTEGER_NUMBER",
            "REAL_NUMBER",
            "NEGATIVE_INTEGER_NUMBER",
            "NEGATIVE_REAL_NUMBER",
        ]:
            value = self.current_token.value
            self.eat(self.current_token.type)
            return Node(name="Number", value=value)
        elif self.current_token.type == "IDENTIFIER":
            identifier = self.current_token.value
            self.eat("IDENTIFIER")
            return Node(name="Identifier", value=identifier)
        else:
            raise Exception(f"Unexpected token {self.current_token.type}")

    def render_tree(self, ast):
        tree_str = ""
        for pre, _, node in RenderTree(ast):
            tree_str += "%s%s\n" % (pre, node)
        return tree_str


# Example usage
if __name__ == "__main__":
    import sys
    from pathlib import Path
    from anytree.exporter import DotExporter
    from lexer import get_lexical_analysis

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
            tkns, errs = get_lexical_analysis(file_path)

            parser = Parser(tkns)
            ast = parser.parse()

            # Render the tree as a string
            tree_str = parser.render_tree(ast)

            print(tree_str)

            # Optionally, export the tree to a file (e.g., a dot file for visualization)
            DotExporter(ast).to_dotfile("ast.dot")
