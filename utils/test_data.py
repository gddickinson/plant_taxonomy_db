"""
Test data for offline development and testing.

Contains sample taxonomic data that mimics ITIS responses.
"""

from models.taxonomy import Taxon


# Sample plant taxa for testing
SAMPLE_TAXA = {
    'arabidopsis_thaliana': {
        'tsn': 505310,
        'scientific_name': 'Arabidopsis thaliana',
        'authorship': '(L.) Heynh.',
        'rank': 'Species',
        'common_names': ['thale cress', 'mouse-ear cress'],
        'lineage': [
            Taxon(
                scientific_name='Plantae',
                rank='Kingdom',
                tsn=202422,
                kingdom='Plantae',
                parent_tsn=None,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Tracheophyta',
                rank='Division',
                tsn=846492,
                kingdom='Plantae',
                division='Tracheophyta',
                parent_tsn=202422,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Magnoliopsida',
                rank='Class',
                tsn=18063,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                parent_tsn=846492,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Brassicales',
                rank='Order',
                tsn=500059,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Brassicales',
                parent_tsn=18063,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Brassicaceae',
                rank='Family',
                tsn=23061,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Brassicales',
                family='Brassicaceae',
                parent_tsn=500059,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Arabidopsis',
                rank='Genus',
                tsn=23144,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Brassicales',
                family='Brassicaceae',
                genus='Arabidopsis',
                parent_tsn=23061,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Arabidopsis thaliana',
                rank='Species',
                tsn=505310,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Brassicales',
                family='Brassicaceae',
                genus='Arabidopsis',
                species='thaliana',
                authorship='(L.) Heynh.',
                parent_tsn=23144,
                source='ITIS',
                common_names=['thale cress', 'mouse-ear cress']
            )
        ]
    },
    'rosa_rugosa': {
        'tsn': 24803,
        'scientific_name': 'Rosa rugosa',
        'authorship': 'Thunb.',
        'rank': 'Species',
        'common_names': ['rugosa rose', 'Japanese rose'],
        'lineage': [
            Taxon(
                scientific_name='Plantae',
                rank='Kingdom',
                tsn=202422,
                kingdom='Plantae',
                parent_tsn=None,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Tracheophyta',
                rank='Division',
                tsn=846492,
                kingdom='Plantae',
                division='Tracheophyta',
                parent_tsn=202422,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Magnoliopsida',
                rank='Class',
                tsn=18063,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                parent_tsn=846492,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Rosales',
                rank='Order',
                tsn=24575,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Rosales',
                parent_tsn=18063,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Rosaceae',
                rank='Family',
                tsn=24578,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Rosales',
                family='Rosaceae',
                parent_tsn=24575,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Rosa',
                rank='Genus',
                tsn=24779,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Rosales',
                family='Rosaceae',
                genus='Rosa',
                parent_tsn=24578,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Rosa rugosa',
                rank='Species',
                tsn=24803,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Rosales',
                family='Rosaceae',
                genus='Rosa',
                species='rugosa',
                authorship='Thunb.',
                parent_tsn=24779,
                source='ITIS',
                common_names=['rugosa rose', 'Japanese rose']
            )
        ]
    },
    'solanum_lycopersicum': {
        'tsn': 30521,
        'scientific_name': 'Solanum lycopersicum',
        'authorship': 'L.',
        'rank': 'Species',
        'common_names': ['tomato'],
        'lineage': [
            Taxon(
                scientific_name='Plantae',
                rank='Kingdom',
                tsn=202422,
                kingdom='Plantae',
                parent_tsn=None,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Tracheophyta',
                rank='Division',
                tsn=846492,
                kingdom='Plantae',
                division='Tracheophyta',
                parent_tsn=202422,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Magnoliopsida',
                rank='Class',
                tsn=18063,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                parent_tsn=846492,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Solanales',
                rank='Order',
                tsn=30403,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Solanales',
                parent_tsn=18063,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Solanaceae',
                rank='Family',
                tsn=30410,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Solanales',
                family='Solanaceae',
                parent_tsn=30403,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Solanum',
                rank='Genus',
                tsn=30454,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Solanales',
                family='Solanaceae',
                genus='Solanum',
                parent_tsn=30410,
                source='ITIS'
            ),
            Taxon(
                scientific_name='Solanum lycopersicum',
                rank='Species',
                tsn=30521,
                kingdom='Plantae',
                division='Tracheophyta',
                class_name='Magnoliopsida',
                order='Solanales',
                family='Solanaceae',
                genus='Solanum',
                species='lycopersicum',
                authorship='L.',
                parent_tsn=30454,
                source='ITIS',
                common_names=['tomato']
            )
        ]
    }
}


def get_test_taxon(name: str) -> dict:
    """Get test taxon data by name."""
    return SAMPLE_TAXA.get(name)


def get_all_test_taxa() -> list:
    """Get all test taxa."""
    return list(SAMPLE_TAXA.values())
