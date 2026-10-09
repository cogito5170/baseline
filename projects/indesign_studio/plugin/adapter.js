// UXP adapter (status: unverified)
// This file runs inside InDesign's UXP environment.
const { app } = require("indesign");

async function create_text_frame(bounds_pt, text, paragraph_style) {
    // STATUS: unverified
    const doc = app.activeDocument;
    const page = doc.pages.item(0);
    const frame = page.textFrames.add();
    frame.geometricBounds = bounds_pt;
    frame.contents = text;
    // Update revision label
    let rev = parseInt(doc.extractLabel("revision_counter") || "0");
    doc.insertLabel("revision_counter", (rev + 1).toString());
    return frame.id;
}

async function inspect() {
    // STATUS: unverified
    const doc = app.activeDocument;
    const report = {
        structural_findings: [],
        visual_findings: []
    };
    const page = doc.pages.item(0);
    for (let i = 0; i < page.textFrames.length; i++) {
        let frame = page.textFrames.item(i);
        if (frame.overflows) {
            report.structural_findings.push({
                id: "err_" + frame.id,
                item_id: frame.id.toString(),
                severity: "error",
                evidence: "Text overflows frame"
            });
        }
    }
    return report;
}
