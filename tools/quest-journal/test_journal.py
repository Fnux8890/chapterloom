import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

import journal


class JournalSDK(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.pack = self.folder/"survey"
        journal.init(self.pack, "survey", "Survey")
        self.data = self.pack/"data/survey"

    def mutate(self, relative, **updates):
        path = self.data/relative
        value = journal.read(path)
        value.update(updates)
        journal.write(self.data, relative, value)

    def test_portable_reproducible_archive(self):
        a, b = self.folder/"a.zip", self.folder/"b.zip"
        for dest in (a,b):
            journal.archive(self.pack, dest, [])
        self.assertEqual(a.read_bytes(), b.read_bytes())
        with ZipFile(a) as z:
            self.assertIn("pack.mcmeta", z.namelist())
            self.assertIn("data/survey/tags/function/api/v1/job_completed.json", z.namelist())
        with self.assertRaisesRegex(ValueError, "exists"):
            journal.archive(self.pack, a, [])
        with self.assertRaisesRegex(ValueError, "exists"):
            journal.init(self.pack, "survey", "Lost")

    def test_shared_parent_and_pack_precedence(self):
        ext = self.folder/"extension"
        journal.write(ext,"pack.mcmeta",journal.read(self.pack/"pack.mcmeta"))
        child = journal.read(self.data/"advancement/first_job.json")
        journal.write(ext,"data/guest/advancement/child.json",child)
        with self.assertRaisesRegex(ValueError,"unresolved parent"):
            journal.validate([ext])
        self.assertEqual((1,4),journal.validate([self.pack,ext]))

    def test_rule_override_and_registry_validation(self):
        ext = self.folder/"expert"
        journal.write(ext, "pack.mcmeta", journal.read(self.pack/"pack.mcmeta"))
        rule = {"version":1,"action":"craft","scope":"player","output":"minecraft:blast_furnace",
                "requires":{"quest_completed":"survey:first_job"}}
        path = "data/test/progression_rule/furnace.json"
        journal.write(self.pack, path, {**rule, "unexpected": True})
        journal.write(ext, path, rule)
        resources = self.folder/"resources"
        journal.write(resources, "items.json", {"minecraft:blast_furnace": {}})
        self.assertEqual((1,3),journal.validate([self.pack, ext], resources))
        for prop in ({"version":True}, {"scope":"machine"}, {"output":"test:typo"},
                     {"requires":{"quest_completed":"survey:missing"}}, {"extra":1}):
            journal.write(ext, path, {**rule, **prop})
            with self.subTest(prop=prop), self.assertRaises(ValueError):
                journal.validate([self.pack, ext], resources)

    def test_bad_graph(self):
        self.mutate("advancement/first_job.json",parent="survey:first_job")
        with self.assertRaisesRegex(ValueError,"cycle"):
            journal.validate([self.pack])

    def test_invalid_manifest_does_not_publish(self):
        output = self.folder/"bad.zip"
        for prop, value in (("version",2),("version",True),("order",32768),("positions",{"survey:missing":[0,0]})):
            with self.subTest(prop=prop,value=value):
                journal.write(self.data,"quest_chapter/journal.json",{"root":"survey:root","version":1,prop:value})
                with self.assertRaises(ValueError):
                    journal.archive(self.pack,output,[])
                self.assertFalse(output.exists())

    def test_requirements_and_duplicate_keys(self):
        self.mutate("advancement/iron_supply.json",requirements=[["typo"]])
        with self.assertRaisesRegex(ValueError,"requirements"):
            journal.validate([self.pack])
        (self.data/"advancement/iron_supply.json").write_text('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError,"duplicate"):
            journal.validate([self.pack])

    def test_manual_retains_payload_and_original_progress_id(self):
        rewards = {"experience":10, "loot":["survey:rewards/brick"], "function":"survey:celebrate"}
        self.mutate("advancement/first_job.json", rewards=rewards)
        out = self.folder/"compiled"
        journal.manual(self.pack, out, ["survey:first_job"])
        src = journal.read(self.data/"advancement/first_job.json")
        dst = out/"data/survey/advancement"
        quest = journal.read(dst/"first_job.json")
        self.assertEqual(quest["criteria"], src["criteria"])
        self.assertEqual(quest["parent"], src["parent"])
        self.assertEqual(src["rewards"], rewards)
        self.assertEqual(journal.read(dst/"journal_claim/first_job/receipt.json")["rewards"], rewards)
        self.assertEqual(quest["rewards"], {"function":"survey:journal_claim/first_job/earn"})
        self.assertEqual(journal.validate([out]), (1,5))

    def test_manual_generation_does_not_leave_partial_output(self):
        out = self.folder/"compiled"
        with self.assertRaisesRegex(ValueError,"already manual"):
            journal.manual(self.pack, out, ["survey:first_job","survey:first_job"])
        self.assertFalse(out.exists())

    def test_format(self):
        journal.write(self.pack,"pack.mcmeta",{"pack":{"min_format":1,"max_format":10}})
        with self.assertRaisesRegex(ValueError,"121"):
            journal.validate([self.pack])


if __name__ == "__main__":
    unittest.main()
