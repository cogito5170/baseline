# InDesign Capabilities Matrix

| Operation | Method / Property | Doc URL | Min Version | Status |
|---|---|---|---|---|
| Document Access | `app.documents.add()`, `app.activeDocument`, `app.open()` | https://developer.adobe.com/indesign/uxp/reference/core/app/documents/ | InDesign 18.0 / UXP 7.0 | documented_unverified |
| Page Creation | `document.pages.add()` | https://developer.adobe.com/indesign/uxp/reference/core/document/pages/ | InDesign 18.0 / UXP 7.0 | documented_unverified |
| Text Frame | `page.textFrames.add()` | https://developer.adobe.com/indesign/uxp/reference/core/page/textFrames/ | InDesign 18.0 / UXP 7.0 | documented_unverified |
| Image Placement | `pageItem.place()` | https://developer.adobe.com/indesign/uxp/reference/core/pageItem/place/ | InDesign 18.0 / UXP 7.0 | documented_unverified |
| Overflow Check | `textFrame.overflows` | https://developer.adobe.com/indesign/uxp/reference/core/textFrame/overflows/ | InDesign 18.0 / UXP 7.0 | documented_unverified |
| Save | `document.save()` | https://developer.adobe.com/indesign/uxp/reference/core/document/save/ | InDesign 18.0 / UXP 7.0 | documented_unverified |
| PDF Export | `document.exportFile()` | https://developer.adobe.com/indesign/uxp/reference/core/document/exportFile/ | InDesign 18.0 / UXP 7.0 | documented_unverified |
| Document Label | `document.insertLabel()`, `document.extractLabel()` | https://developer.adobe.com/indesign/uxp/reference/core/document/insertLabel/ | InDesign 18.0 / UXP 7.0 | documented_unverified |

## Route A: Sidekick Integration

Route A relies on the `sidekick-indesign` MCP server. We maintain a mapping in `sidekick_tools.json` from our operations to the server's tools.
Currently, all tools are placeholders and marked `unverified` until `tools/list` output is provided by the user.
