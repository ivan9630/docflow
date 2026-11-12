import unittest,csv
from agent.diagnostic_agent import decision,run
from agent.rag_knowledge import Knowledge
class Tests(unittest.TestCase):
    def test_risque(self):
        self.assertEqual(decision({"defauts":"surchauffe","etat":"bon","valeur_estimee":200}),"recycler")
    def test_reemploi(self):
        self.assertEqual(decision({"defauts":"cosmetique","etat":"bon","valeur_estimee":130}),"reconditionner")
    def test_rag(self):
        self.assertTrue(len(Knowledge().search("reemploi"))>0)
    def test_80(self):
        self.assertEqual(len(run()),80)
if __name__=="__main__":unittest.main()
