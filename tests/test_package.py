import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT/'plugins/pmu-swarm'
SKILL = PLUGIN/'skills/pmu-swarm'

class PackageTest(unittest.TestCase):
    def read(self, path): return json.loads(path.read_text())

    def test_plugin_identity_and_versions_agree(self):
        manifests=[self.read(PLUGIN/p) for p in ('plugin.json','.claude-plugin/plugin.json','.codex-plugin/plugin.json')]
        self.assertEqual({m['name'] for m in manifests},{'pmu-swarm'})
        self.assertEqual({m['version'] for m in manifests},{'1.0.0'})
        self.assertTrue((PLUGIN/self.read(PLUGIN/'.codex-plugin/plugin.json')['skills']).is_dir())

    def test_marketplaces_resolve_plugin(self):
        claude=self.read(ROOT/'.claude-plugin/marketplace.json')
        codex=self.read(ROOT/'.agents/plugins/marketplace.json')
        self.assertEqual(claude['name'],codex['name'])
        self.assertTrue(claude['owner']['name'])
        for entry,path in [(claude['plugins'][0],claude['plugins'][0]['source']),(codex['plugins'][0],codex['plugins'][0]['source']['path'])]:
            self.assertEqual(entry['name'],'pmu-swarm')
            self.assertTrue(path.startswith('./'))
            self.assertEqual((ROOT/path).resolve(),PLUGIN.resolve())

    def test_skill_references_exist_and_no_placeholders(self):
        content=(SKILL/'SKILL.md').read_text()
        self.assertTrue(content.startswith('---\nname: pmu-swarm\n'))
        self.assertNotIn('TODO',content)
        for link in re.findall(r'\]\((references/[^)]+)\)',content):
            self.assertTrue((SKILL/link).is_file(),link)
        self.assertTrue((SKILL/'scripts/pmu_state.py').is_file())
        self.assertIn('$pmu-swarm',(SKILL/'agents/openai.yaml').read_text())

if __name__ == '__main__': unittest.main()
