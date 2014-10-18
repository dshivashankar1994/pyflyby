# pyflyby/test_imports2s.py

# License for THIS FILE ONLY: CC0 Public Domain Dedication
# http://creativecommons.org/publicdomain/zero/1.0/

from __future__ import absolute_import, division, with_statement

import sys
from   textwrap                 import dedent
import types

from   pyflyby.importdb         import ImportDB
from   pyflyby.imports2s        import (canonicalize_imports,
                                        fix_unused_and_missing_imports,
                                        reformat_import_statements,
                                        remove_broken_imports,
                                        replace_star_imports,
                                        transform_imports)
from   pyflyby.parse            import PythonBlock


def test_reformat_import_statements_1():
    input = PythonBlock(dedent('''
        from foo import bar2 as bar2x, bar1
        import foo.bar3 as bar3x
        import foo.bar4

        import foo.bar0 as bar0
    ''').lstrip(), filename="/foo/test_reformat_import_statements_1.py")
    output = reformat_import_statements(input)
    expected = PythonBlock(dedent('''
        import foo.bar4
        from foo import bar1, bar2 as bar2x, bar3 as bar3x

        from foo import bar0
    ''').lstrip(), filename="/foo/test_reformat_import_statements_1.py")
    assert output == expected


def test_reformat_import_statements_star_1():
    input = PythonBlock(dedent('''
        from mod1 import f1b
        from mod1 import f1a
        from mod2 import *
        from mod2 import f2b as F2B
        from mod2 import f2a as F2A
        from mod3 import f3b
        from mod3 import f3a
    ''').lstrip(), filename="/foo/test_reformat_import_statements_star_1.py")
    output = reformat_import_statements(input)
    expected = PythonBlock(dedent('''
        from mod1 import f1a, f1b
        from mod2 import *
        from mod2 import f2a as F2A, f2b as F2B
        from mod3 import f3a, f3b
    ''').lstrip(), filename="/foo/test_reformat_import_statements_star_1.py")
    assert output == expected


def test_reformat_import_statements_multi_star_1():
    input = PythonBlock(dedent('''
        from mod1 import *
        from mod2 import *
    ''').lstrip())
    output = reformat_import_statements(input)
    expected = PythonBlock(dedent('''
        from mod1 import *
        from mod2 import *
    ''').lstrip())
    assert output == expected


def test_reformat_import_statements_shadowed_1():
    input = PythonBlock(dedent('''
        import a, a2 as a, b, b2 as b, b, c2 as c, d2 as d
        from d import d
        import c
    ''').lstrip())
    output = reformat_import_statements(input)
    expected = PythonBlock(dedent('''
        import a2 as a
        import b
        import c
        from d import d
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_1():
    input = PythonBlock(dedent('''
        from foo import m1, m2, m3, m4
        m2, m4, np.foo
    ''').lstrip(), filename="/foo/test_fix_unused_and_missing_imports_1.py")
    db = ImportDB("""
        import numpy as np
        __mandatory_imports__ = ["from __future__ import division"]
    """)
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from __future__ import division

        import numpy as np
        from foo import m2, m4
        m2, m4, np.foo
    ''').lstrip(), filename="/foo/test_fix_unused_and_missing_imports_1.py")
    assert output == expected


def test_fix_unused_and_missing_imports_unknown_1():
    input = PythonBlock(dedent('''
        os, sys
    ''').lstrip())
    db = ImportDB("import os")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        import os

        os, sys
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_known_different_1():
    input = PythonBlock(dedent('''
        from ma import a1, a2
        from mb import b1, b2
        a1, a2, a3, b1, b2, b3
    ''').lstrip())
    db = ImportDB("from MA import a1, a2, a3\nfrom MB import b1, b2, b3\n")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from MA import a3
        from MB import b3
        from ma import a1, a2
        from mb import b1, b2
        a1, a2, a3, b1, b2, b3
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_insertion_heuristic_1():
    input = PythonBlock(dedent('''
        from m1.a import f1
        from m2.a import f2
        from m3.a import f3
        f1, f2, f3, f4
    ''').lstrip())
    db = ImportDB("from m2.b import f4")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from m1.a import f1
        from m2.a import f2
        from m2.b import f4
        from m3.a import f3
        f1, f2, f3, f4
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_insertion_after_comments_1():
    input = PythonBlock(dedent('''
        # hello

        # there
        f1, f2
    ''').lstrip())
    db = ImportDB("from m1 import f1")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        # hello

        # there
        from m1 import f1

        f1, f2
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_insertion_after_docstring_1():
    input = PythonBlock(dedent('''
        """
        aaa
        """
        f1, f2
    ''').lstrip())
    db = ImportDB("from m1 import f1")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        """
        aaa
        """
        from m1 import f1

        f1, f2
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_insertion_after_docstring_cont_1():
    input = PythonBlock(dedent('''
        """
        aaa
        """ '\
        bbb'
        f1, f2
    ''').lstrip())
    db = ImportDB("from m1 import f1")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        """
        aaa
        """ '\
        bbb'
        from m1 import f1

        f1, f2
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_insertion_after_docstring_whitespace_1():
    input = PythonBlock(dedent('''
        """
        aaa
        """


        f1, f2
    ''').lstrip())
    db = ImportDB("from m1 import f1")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        """
        aaa
        """


        from m1 import f1

        f1, f2
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_insertion_comments_1():
    input = PythonBlock(dedent('''
        #c0
        from m1.y import m1yf
        #c1
        from m2.y import m2yf
        #c2
        from m3.y import m3yf
        #c3
        m1xf, m2xf, m3xf
        m1yf, m2yf, m3yf
        m1zf, m2zf, m3zf
    ''').lstrip())
    db = ImportDB("""
        from m1.x import m1xf
        from m1.y import m1yf
        from m1.z import m1zf
        from m2.x import m2xf
        from m2.y import m2yf
        from m2.z import m2zf
        from m3.x import m3xf
        from m3.y import m3yf
        from m3.z import m3zf
    """)
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        #c0
        from m1.x import m1xf
        from m1.y import m1yf
        from m1.z import m1zf
        #c1
        from m2.x import m2xf
        from m2.y import m2yf
        from m2.z import m2zf
        #c2
        from m3.x import m3xf
        from m3.y import m3yf
        from m3.z import m3zf
        #c3
        m1xf, m2xf, m3xf
        m1yf, m2yf, m3yf
        m1zf, m2zf, m3zf
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_compound_statements_1():
    input = PythonBlock(dedent('''
        import a, b; import c, d; g
        a, c; f
    ''').lstrip())
    db = ImportDB("""
        from m1 import f
        from m1 import g
    """)
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        import a
        import c
        from m1 import f, g
        g
        a, c; f
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_multiple_import_used_1():
    input = PythonBlock(dedent('''
        from m0 import f, x
        import z, x
        import y, z
        from m1 import h, f
        import x
        import x
        from m1 import f, f, g
        x, f
    ''').lstrip())
    db = ImportDB("")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        import x
        from m1 import f
        x, f
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_shadowed_1():
    input = PythonBlock(dedent('''
        from m1 import f1, f2, f3
        def f2(): f1
    ''').lstrip())
    db = ImportDB("")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from m1 import f1
        def f2(): f1
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_midfile_1():
    input = PythonBlock(dedent('''
        import m1, m2
        m2, m3
        import m4, m5
        m4, m6
    ''').lstrip())
    db = ImportDB("import m1, m2, m3, m4, m5, m6, m7")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        import m2
        import m3
        m2, m3
        import m4
        import m6
        m4, m6
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_doctests_1():
    input = PythonBlock(dedent('''
        from m1 import f1, f2, f3
        def foo():
            """
              >>> f1 + f2 + f9
            """
            return None
    ''').lstrip())
    db = ImportDB("")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from m1 import f1, f2
        def foo():
            """
              >>> f1 + f2 + f9
            """
            return None
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_doctests_2():
    input = PythonBlock(dedent('''
        from m1 import f1, f2, f3
        def foo():
            """
              >>> f1 = 0
              >>> f1 + f2 + f9
            """
            return None
    ''').lstrip())
    db = ImportDB("")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from m1 import f2
        def foo():
            """
              >>> f1 = 0
              >>> f1 + f2 + f9
            """
            return None
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_xref_1():
    input = PythonBlock(dedent('''
        from m1 import f1, f2, f3
        def foo():
            """
            Hello L{f1} C{f3}
            """
            return None
    ''').lstrip())
    db = ImportDB("")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from m1 import f1, f3
        def foo():
            """
            Hello L{f1} C{f3}
            """
            return None
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_decorator_2():
    input = PythonBlock(dedent('''
        from m1 import d1, d2, d3
        @d1
        def f1(): pass
        @d9.d2
        def f9(): pass
    ''').lstrip())
    db = ImportDB("from m2 import d8, d9")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from m1 import d1
        from m2 import d9
        @d1
        def f1(): pass
        @d9.d2
        def f9(): pass
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_funcall_1():
    input = PythonBlock(dedent('''
        from m1 import X1, X3, X9
        def F1(X1, X2=x2, X3=x3, *X4, **X5): X1, X5, x6, X9
        def F2(X7=x7): X7
        def F3(a1): a1
        def F4(): a1
    ''').lstrip())
    db = ImportDB("from m2 import x1, x2, x3, x4, x5, x6, x7, a1, a2")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from m1 import X9
        from m2 import a1, x2, x3, x6, x7
        def F1(X1, X2=x2, X3=x3, *X4, **X5): X1, X5, x6, X9
        def F2(X7=x7): X7
        def F3(a1): a1
        def F4(): a1
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_IfExp_1():
    input = PythonBlock(dedent('''
        x if y else z
    ''').lstrip())
    db = ImportDB("from m1 import w, x, y, z")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from m1 import x, y, z

        x if y else z
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_imports_ClassDef_1():
    input = PythonBlock(dedent('''
        @x1
        class x2(x3(x4), x5):
            @x6
            def x7(x8=x9): x10, x8
            def x11(): x11
    ''').lstrip())
    db = ImportDB("from m1 import x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from m1 import x1, x10, x11, x3, x4, x5, x6, x9

        @x1
        class x2(x3(x4), x5):
            @x6
            def x7(x8=x9): x10, x8
            def x11(): x11
    ''').lstrip())
    assert output == expected


def test_fix_unused_and_missing_continutation_1():
    input = PythonBlock(dedent(r'''
        a#\
        b + '\
        c#' + d
    ''').lstrip())
    db = ImportDB("from m1 import a, b, c, d")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent(r'''
        from m1 import a, b, d

        a#\
        b + '\
        c#' + d
    ''').lstrip())
    assert output == expected


def test_last_line_no_trailing_newline_1():
    input = PythonBlock("#x\ny")
    db = ImportDB("from Y import y")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        #x
        from Y import y

        y''').lstrip())
    assert output == expected


def test_last_line_comment_no_trailing_newline_1():
    input = PythonBlock("y\n#x")
    db = ImportDB("from Y import y")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from Y import y

        y
        #x''').lstrip())
    assert output == expected


def test_last_line_multistring_no_trailing_newline_1():
    input = PythonBlock(dedent('''
        """
        #x""", y # comment  ''').lstrip())
    db = ImportDB("from Y import y")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from Y import y

        """
        #x""", y # comment  ''').lstrip())
    assert output == expected


def test_last_line_escaped_string_no_trailing_newline_1():
    input = PythonBlock(dedent('''
        "\
        #x", y # comment  ''').lstrip())
    db = ImportDB("from Y import y")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from Y import y

        "\
        #x", y # comment  ''').lstrip())
    assert output == expected


def test_remove_broken_imports_1():
    input = PythonBlock(dedent('''
        import sys, os, omgdoesntexist_95421787, keyword
        from email import MIMEAudio, omgdoesntexist_8824165
        code()
    ''').lstrip(), filename="/foo/test_remove_broken_imports_1.py")
    output = remove_broken_imports(input)
    expected = PythonBlock(dedent('''
        import keyword
        import os
        import sys
        from email import MIMEAudio
        code()
    ''').lstrip(), filename="/foo/test_remove_broken_imports_1.py")
    assert output == expected


def test_replace_star_imports_1():
    m = types.ModuleType("fake_test_module_345489")
    m.__all__ = ['f1', 'f2', 'f3', 'f4', 'f5']
    sys.modules["fake_test_module_345489"] = m
    input = PythonBlock(dedent('''
        from mod1                    import f1
        from fake_test_module_345489 import *
        from mod2                    import f5
    ''').lstrip(), filename="/foo/test_replace_star_imports_1.py")
    output = replace_star_imports(input)
    expected = PythonBlock(dedent('''
        from fake_test_module_345489 import f1, f2, f3, f4
        from mod2                    import f5
    ''').lstrip(), filename="/foo/test_replace_star_imports_1.py")
    assert output == expected


def test_replace_star_imports_relative_1():
    # Not implemented (semi-intentionally), but at least don't crash.
    input = PythonBlock(dedent('''
        from .x import *
    ''').lstrip(), filename="/foo/test_replace_star_imports_relative_1.py")
    output = replace_star_imports(input)
    expected = PythonBlock(dedent('''
        from .x import *
    ''').lstrip(), filename="/foo/test_replace_star_imports_relative_1.py")
    assert output == expected


def test_replace_star_imports_unknown_module_1():
    input = PythonBlock(dedent('''
        from omgnonexistentmodule75085477 import *
    ''').lstrip())
    output = replace_star_imports(input)
    expected = PythonBlock(dedent('''
        from omgnonexistentmodule75085477 import *
    ''').lstrip())
    assert output == expected


def test_transform_imports_1():
    input = PythonBlock(dedent('''
        from m import x
        from m import x as X
        import m.x
        print m.x, m.xx
    ''').lstrip(), filename="/foo/test_transform_imports_1.py")
    output = transform_imports(input, {"m.x": "m.y.z"})
    expected = PythonBlock(dedent('''
        import m.y.z
        from m.y import z as X, z as x
        print m.y.z, m.xx
    ''').lstrip(), filename="/foo/test_transform_imports_1.py")
    assert output == expected


def test_canonicalize_imports_1():
    input = PythonBlock(dedent('''
        from m import x
        from m import x as X
        import m.x
        print m.x, m.xx
    ''').lstrip(), filename="/foo/test_transform_imports_1.py")
    db = ImportDB("""
        __canonical_imports__ = {"m.x": "m.y.z"}
    """)
    output = canonicalize_imports(input, db=db)
    expected = PythonBlock(dedent('''
        import m.y.z
        from m.y import z as X, z as x
        print m.y.z, m.xx
    ''').lstrip(), filename="/foo/test_transform_imports_1.py")
    assert output == expected


def test_empty_file_1():
    input = PythonBlock('', filename="/foo/test_empty_file_1.py")
    db = ImportDB("")
    output = canonicalize_imports(input, db=db)
    expected = PythonBlock('', filename="/foo/test_empty_file_1.py")
    assert output == expected


def test_empty_file_mandatory_1():
    input = PythonBlock('', filename="/foo/test_empty_file_mandatory_1.py")
    db = ImportDB("__mandatory_imports__ = ['from aa import cc,bb']")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock('from aa import bb, cc\n\n',
                           filename="/foo/test_empty_file_mandatory_1.py")
    assert output == expected


def test_future_flags_1():
    input = PythonBlock(dedent('''
        from __future__ import print_function

        print("", file=sys.stdout)
    ''').lstrip())
    db = ImportDB("import os, sys")
    output = fix_unused_and_missing_imports(input, db=db)
    expected = PythonBlock(dedent('''
        from __future__ import print_function
        import sys

        print("", file=sys.stdout)
    ''').lstrip())
    assert output == expected
