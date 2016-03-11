"""Interface tests for Treants.

"""

import datreant.core as dtr
import pytest
import os
import py

from . import test_bundle
from .test_trees import TestTree


class TestTreant(TestTree):
    """Test generic Treant features"""
    treantname = 'testtreant'
    treanttype = 'Treant'

    @pytest.fixture
    def treantclass(self):
        return dtr.treants.Treant

    @pytest.fixture
    def treant(self, tmpdir):
        with tmpdir.as_cwd():
            c = dtr.treants.Treant(TestTreant.treantname)
        return c

    def test_init(self, treant, tmpdir):
        """Test basic Treant init"""
        assert treant.name == self.treantname
        assert treant.location == tmpdir.strpath
        assert treant.treanttype == self.treanttype
        assert treant.abspath == (os.path.join(tmpdir.strpath,
                                               self.treantname) + os.sep)

    def test_gen_methods(self, tmpdir, treantclass):
        """Test the variety of ways we can generate a new Treant

        1. ``Treant('treant')``, where 'treant' is not an existing file or
           directory path

        2. ``Treant('treant')``, where 'treant' is an existing directory
           without Treant state files inside

        3. ``Treant('/somedir/treant')``, where 'treant' is not an existing
           file or directory in 'somedir'

        4. ``Treant('/somedir/treant')``, where 'treant' is an existing
           directory in 'somedir' without any Treant state files inside

        5. ``Treant('somedir/treant', new=True)``, where 'treant' is an
           existing directory in 'somedir' with an existing Treant statefile

        6. ``Treant('/somedir/treant')``, where 'treant' is an existing
           directory in 'somedir' with other types of Treant files inside (such
           as Group)

        """
        with tmpdir.as_cwd():
            # 1
            t1 = treantclass('newone')
            assert os.path.exists(t1.filepath)

            # 2
            os.mkdir('another')
            t2 = treantclass('another')
            assert os.path.exists(t2.filepath)

            # 3
            t3 = treantclass('yet/another')
            assert os.path.exists(t3.filepath)

            # 4
            os.mkdir('yet/more')
            t4 = treantclass('yet/more')
            assert os.path.exists(t4.filepath)

            # 5
            t5 = treantclass('yet/more', new=True)
            assert os.path.exists(t5.filepath)
            assert t5.abspath == t4.abspath
            assert t5.filepath != t4.filepath

            # 6
            compare = t1.uuid
            os.rename(t1.filepath,
                      t1.filepath.replace(t1.treanttype, 'Another'))
            t6 = treantclass('newone')
            assert t6.uuid != compare

    def test_regen(self, tmpdir, treantclass):
        """Test regenerating Treant.

        - create Treant
        - modify Treant a little
        - create same Treant (should regenerate)
        - check that modifications were saved
        """
        with tmpdir.as_cwd():
            C1 = treantclass('regen')
            C1.tags.add('fantastic')
            C2 = treantclass('regen')  # should be regen of C1
            assert 'fantastic' in C2.tags

            # they point to the same file, but they are not the same object
            assert C1 is not C2

    def test_regen_methods(self, tmpdir, treantclass):
        """Test the variety of ways Treants can be regenerated.

        1. ``Treant('treant')``, where there exists *only one* ``Treant`` state
           file inside 'treant'

        2. ``Treant('treant/Treant.<uuid>.<ext>')``, where there need not be
           only a single ``Treant`` state file in 'treant'

        """
        with tmpdir.as_cwd():
            t1 = treantclass('newone')
            t2 = treantclass('newone')
            assert t1.uuid == t2.uuid

            t3 = treantclass('newone', new=True)
            assert t3.uuid != t2.uuid

            t4 = treantclass(t3.filepath)
            assert t4.uuid == t3.uuid

    def test_noregen(self, tmpdir, treantclass):
        """Test a variety of ways that generation of a new Treant should fail.

        1. `Treant('somedir/treant')` should raise `MultipleTreantsError` if
           more than one state file is in the given directory

        """
        with tmpdir.as_cwd():
            # 1
            t1 = treantclass('newone')
            t2 = treantclass('newone', new=True)
            assert t1.uuid != t2.uuid

            with pytest.raises(dtr.treants.MultipleTreantsError):
                t3 = treantclass('newone')

    def test_cmp(self, tmpdir, treantclass):
        """Test the comparison of Treants when sorting"""
        with tmpdir.as_cwd():
            c1 = treantclass('a')
            c2 = treantclass('b')
            c3 = treantclass('c')

        assert sorted([c3, c2, c1]) == [c1, c2, c3]
        assert c1 <= c2 < c3
        assert c3 >= c2 > c1

    class TestTags:
        """Test treant tags"""

        def test_add_tags(self, treant):
            treant.tags.add('marklar')
            assert 'marklar' in treant.tags

            treant.tags.add('lark', 'bark')
            assert 'marklar' in treant.tags
            assert 'lark' in treant.tags
            assert 'bark' in treant.tags

        def test_remove_tags(self, treant):
            treant.tags.add('marklar')
            assert 'marklar' in treant.tags
            treant.tags.remove('marklar')
            assert 'marklar' not in treant.tags

            treant.tags.add('marklar')
            treant.tags.add('lark', 'bark')
            treant.tags.add(['fark', 'bark'])
            assert 'marklar' in treant.tags
            assert 'lark' in treant.tags
            assert 'bark' in treant.tags
            assert 'fark' in treant.tags
            assert len(treant.tags) == 4

            treant.tags.remove('fark')
            assert 'fark' not in treant.tags
            assert len(treant.tags) == 3
            treant.tags.remove('fark')
            assert len(treant.tags) == 3

            treant.tags.clear()
            assert len(treant.tags) == 0

        def test_tags_set_behavior(self, tmpdir, treantclass):

            with tmpdir.as_cwd():
                # 1
                t1 = treantclass('maple')
                assert os.path.exists(t1.filepath)
                t1.tags.add(['sprout', 'deciduous'])

                # 2
                t2 = treantclass('sequoia')
                assert os.path.exists(t2.filepath)
                t2.tags.add(['sprout', 'evergreen'])

                tags_union = t1.tags | t2.tags
                for t in ['sprout', 'deciduous', 'evergreen']:
                    assert t in tags_union

                tags_intersect = t1.tags & t2.tags
                for t in ['sprout']:
                    assert t in tags_intersect

                tags_diff = t1.tags - t2.tags
                assert 'deciduous' in tags_diff

                tags_symm_diff = t1.tags ^ t2.tags
                for t in ['deciduous', 'evergreen']:
                    assert t in tags_symm_diff

                # 3
                t3 = treantclass('oak')
                assert os.path.exists(t3.filepath)
                t3.tags.add(['deciduous'])

                tags_subset0 = t1.tags <= t1.tags
                assert tags_subset0 is True
                tags_subset1 = t1.tags < t1.tags
                assert tags_subset1 is False
                tags_subset2 = t1.tags == t1.tags
                assert tags_subset2 is True
                tags_subset3 = t1.tags < t3.tags
                assert tags_subset3 is False
                tags_subset4 = t1.tags > t3.tags
                assert tags_subset4 is True

    class TestCategories:
        """Test treant categories"""

        def test_add_categories(self, treant):
            treant.categories.add(marklar=42)
            assert 'marklar' in treant.categories

            treant.categories.add({'bark': 'snark'}, lark=27)
            assert 'bark' in treant.categories
            assert 'snark' not in treant.categories
            assert 'bark' in treant.categories

            assert treant.categories['bark'] == 'snark'
            assert treant.categories['lark'] == 27

            treant.categories['lark'] = 42
            assert treant.categories['lark'] == 42

        def test_remove_categories(self, treant):
            treant.categories.add(marklar=42)
            assert 'marklar' in treant.categories

            treant.categories.remove('marklar')
            assert 'marklar' not in treant.categories

            treant.categories.add({'bark': 'snark'}, lark=27)
            del treant.categories['bark']
            assert 'bark' not in treant.categories

            # should just work, even if key isn't present
            treant.categories.remove('smark')

            treant.categories['lark'] = 42
            treant.categories['fark'] = 32.3

            treant.categories.clear()
            assert len(treant.categories) == 0

        def test_add_wrong(self, treant):
            with pytest.raises(TypeError):
                treant.categories.add('temperature', 300)

            with pytest.raises(TypeError):
                treant.categories.add(['mark', 'matt'])

        def test_KeyError(self, treant):
            with pytest.raises(KeyError):
                treant.categories['hello?']


class TestGroup(TestTreant):
    """Test Group-specific features.

    """
    treantname = 'testgroup'
    treanttype = 'Group'

    @pytest.fixture
    def treant(self, tmpdir):
        with tmpdir.as_cwd():
            g = dtr.Group(TestGroup.treantname)
        return g

    @pytest.fixture
    def treantclass(self):
        return dtr.treants.Group

    def test_repr(self, treant):
        pass

    class TestMembers(test_bundle.TestBundle):
        """Test member functionality"""

        @pytest.fixture
        def collection(self, treant):
            return treant.members


class TestReadOnly:
    """Test Treant functionality when read-only"""

    @pytest.fixture
    def treant(self, tmpdir, request):
        with tmpdir.as_cwd():
            c = dtr.treants.Treant('testtreant')
            c.tags.add('72')
            py.path.local(c.abspath).chmod(0o0550, rec=True)

        def fin():
            py.path.local(c.abspath).chmod(0o0770, rec=True)

        request.addfinalizer(fin)

        return c

    @pytest.fixture
    def group(self, tmpdir, request):
        with tmpdir.as_cwd():
            c = dtr.Group('testgroup')
            c.members.add(dtr.Treant('lark'), dtr.Group('bark'))
            py.path.local(c.abspath).chmod(0o0550, rec=True)

        def fin():
            py.path.local(c.abspath).chmod(0o0770, rec=True)

        request.addfinalizer(fin)

        return c

    def test_treant_read_only(self, treant):
        """Test that a read-only Treant can be accessed, but not written to.
        """
        c = dtr.treants.Treant(treant.filepath)

        assert '72' in c.tags

        with pytest.raises(OSError):
            c.tags.add('yet another')

    def test_group_member_access(self, group):
        """Test that Group can access members when the Group is read-only.
        """
        assert len(group.members) == 2

    def test_group_moved_member_access(self, group, tmpdir):
        """Test that Group can access members when the Group is read-only,
        and when a member has been moved since the Group was last used with
        write-permissions.
        """
        with tmpdir.as_cwd():
            t = dtr.Treant('lark')
            t.location = 'somewhere/else'

        assert len(group.members) == 2
