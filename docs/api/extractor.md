# Extractor API

## Extraction
::: wpextract.WPExtractor

## Extraction Data


::: wpextract.extractors.data.links
    options:
        show_root_heading: false
        show_root_toc_entry: false
        show_object_full_path: true

## Multilingual Extraction

::: wpextract.parse.translations.LangPicker
    options:
        members:
            - current_language
            - page_doc
            - root_el
            - translations
            - add_translation
            - extract
            - get_root
            - matches
            - set_current_lang
            - _root_select_one
            - _root_select
            - _build_extraction_fail_err

::: wpextract.parse.translations.PickerListType

::: wpextract.parse.translations.TranslationLink
    options:
        inherited_members:
          - destination
          - href

