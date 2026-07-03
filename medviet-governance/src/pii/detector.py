"""Vietnamese PII recognizers used by the MedViet pipeline."""

import spacy
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider, SpacyNlpEngine
from presidio_analyzer.predefined_recognizers import EmailRecognizer


def _build_nlp_engine():
    """Load the Vietnamese NER model, with a lightweight offline fallback."""
    model_name = "vi_core_news_lg"
    if spacy.util.is_package(model_name):
        provider = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "vi", "model_name": model_name}],
            }
        )
        return provider.create_engine()

    # The lab must also work in CI where the optional, large model is absent.
    engine = SpacyNlpEngine(models=[{"lang_code": "vi", "model_name": model_name}])
    # The multilingual tokenizer handles Unicode Vietnamese text without the
    # optional ``pyvi`` package required by ``spacy.blank("vi")``.
    engine.nlp = {"vi": spacy.blank("xx")}
    return engine


def build_vietnamese_analyzer() -> AnalyzerEngine:
    """Build a Presidio analyzer with recognizers tailored for Vietnam."""
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        supported_language="vi",
        patterns=[Pattern("cccd_pattern", r"(?<!\d)\d{12}(?!\d)", 0.9)],
        context=["cccd", "căn cước", "chứng minh", "cmnd"],
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        supported_language="vi",
        patterns=[Pattern("vn_phone", r"(?<!\d)0[35789]\d{8}(?!\d)", 0.85)],
        context=["điện thoại", "sdt", "phone", "liên hệ"],
    )
    # A deterministic fallback for the generated Vietnamese names. A trained
    # spaCy model, when installed, can additionally contribute NER results.
    person_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        supported_language="vi",
        patterns=[
            Pattern(
                "vn_person",
                r"(?<![\w@])(?:[A-ZÀ-ỸĐ][a-zà-ỹđ]+(?:\s+|$)){2,6}",
                0.75,
            )
        ],
        context=["bệnh nhân", "họ tên", "họ và tên", "bác sĩ"],
    )

    analyzer = AnalyzerEngine(
        nlp_engine=_build_nlp_engine(), supported_languages=["vi"]
    )
    for recognizer in (
        cccd_recognizer,
        phone_recognizer,
        person_recognizer,
        EmailRecognizer(supported_language="vi"),
    ):
        analyzer.registry.add_recognizer(recognizer)
    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """Detect the PII types used by the Vietnamese patient dataset."""
    if text is None:
        return []
    return analyzer.analyze(
        text=str(text),
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
    )
