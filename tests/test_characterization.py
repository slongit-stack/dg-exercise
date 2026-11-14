"""Guard against misleading subgroup averages and dropped missing metadata."""
import unittest
from scripts.characterize_performance import metadata_labels, pool, ranking_label


class CharacterizationTests(unittest.TestCase):
    def test_pooled_ratio_not_mean_of_clip_rates(self):
        got=pool([dict(errors=1,reference_mass=1),dict(errors=0,reference_mass=9)])
        self.assertEqual(got['score_percent'],10)
        weighted=pool([dict(errors=2.5,reference_mass=5),dict(errors=0,reference_mass=15)])
        self.assertEqual(weighted['score_percent'],12.5)

    def test_boundaries_and_unannotated_roles_retained(self):
        row=dict(meeting_type='non-scenario',meeting_id='EN2002a',meeting_series_id='EN2002',
                 speaker_id='person',annotation_role=None,duration_seconds=1.74)
        labels=metadata_labels(row,[1.74,2.9,4.93])
        self.assertEqual(labels['annotation_role'],'unannotated')
        self.assertEqual(labels['duration_bin'],'Q2')
        row['duration_seconds']=1.7399
        self.assertEqual(metadata_labels(row,[1.74,2.9,4.93])['duration_bin'],'Q1')

    def test_zero_reference_mass_is_undefined_not_zero_error(self):
        self.assertIsNone(pool([dict(errors=1,reference_mass=0)])['score_percent'])

    def test_equal_scores_are_not_reported_as_strict_order(self):
        self.assertEqual(ranking_label({'large':10,'turbo':10,'parakeet':5}),
                         'parakeet < large = turbo')


if __name__=='__main__':
    unittest.main()
