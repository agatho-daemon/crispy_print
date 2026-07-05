import { describe, expect, it } from "vitest";
import { translateJSONToTypst } from "../../typst/JSONToTypst";

describe("Typst integration", () => {
  it("renders letterhead background and QR foreground", () => {
    const typst = translateJSONToTypst(
      {
        sections: [
          {
            label: "Header",
            columns: [
              {
                label: "",
                fields: [
                  { fieldname: "title", fieldtype: "Data", label: "Title" },
                ],
              },
            ],
          },
        ],
      },
      { image: "/files/letterhead.png", letter_head_name: "Default LH" },
      "Invoice",
      { name: "INV-0001", title: "Test" },
      {
        page: {
          size: "A4",
          orientation: "portrait",
          margins: { top: 10, bottom: 10, left: 10, right: 10 },
        },
        branding: {
          mode: "letterhead",
          letterhead: "Default LH",
          letterhead_image: "",
          logo: { company: "", image: "", size: 25, dx: 0, dy: 0 },
        },
        qrEnabled: true,
        qrFilename: "INV-0001-qr.svg",
      },
    );

    expect(typst).toContain('background: image("letterhead.png", width: 100%)');
    expect(typst).toContain("foreground: [");
    expect(typst).toContain('image("INV-0001-qr.svg"');
    expect(typst).not.toContain('image("logo.png"');
  });

  it("renders logo and QR in foreground for logo mode", () => {
    const typst = translateJSONToTypst(
      {
        sections: [
          {
            label: "Main",
            columns: [
              {
                label: "",
                fields: [
                  { fieldname: "name", fieldtype: "Data", label: "Name" },
                ],
              },
            ],
          },
        ],
      },
      null,
      "Document",
      { name: "DOC-1" },
      {
        branding: {
          mode: "logo",
          letterhead: "",
          letterhead_image: "",
          logo: {
            company: "",
            image: "/files/logo.png",
            size: 30,
            dx: 2,
            dy: 3,
          },
        },
        qrEnabled: true,
        qrFilename: "DOC-1-qr.svg",
      },
    );

    expect(typst).toContain("foreground: [");
    expect(typst).toContain('image("logo.png"');
    expect(typst).toContain('image("DOC-1-qr.svg"');
    expect(typst).not.toContain("background: image(");
  });

  it("renders Crispy Typst Block code when resolved", () => {
    const typst = translateJSONToTypst(
      {
        sections: [
          {
            label: "",
            columns: [
              {
                label: "",
                fields: [
                  {
                    fieldname: "_crispy_typst_block",
                    fieldtype: "Crispy Typst Block",
                    label: "Crispy Typst Block",
                    crispy_typst_block: "invoice_header",
                    crispy_typst_block_code:
                      "#text(weight: 700)[#doc.customer_name]",
                  },
                ],
              },
            ],
          },
        ],
      },
      null,
      "Sales Invoice",
      { name: "INV-1", customer_name: "Alice" },
      {},
    );

    expect(typst).toContain("#text(weight: 700)[#doc.customer_name]");
    expect(typst).not.toContain("Missing Crispy Typst Block");
  });

  it("renders Crispy Image fields through the private image helper", () => {
    const typst = translateJSONToTypst(
      {
        sections: [
          {
            label: "",
            columns: [
              {
                label: "",
                fields: [
                  {
                    fieldname: "_crispy_image",
                    fieldtype: "Crispy Image",
                    label: "Crispy Image",
                    crispy_image: "seal.svg",
                  },
                ],
              },
            ],
          },
        ],
      },
      null,
      "Sales Invoice",
      { name: "INV-1" },
      {},
    );

    expect(typst).toContain("#let crispy_image");
    expect(typst).toContain('#crispy_image("seal.svg", width: 100%)');
    expect(typst).not.toContain("Missing Crispy Image");
  });

  it("renders persisted _crispy_image fields even when fieldtype is generic", () => {
    const typst = translateJSONToTypst(
      {
        sections: [
          {
            label: "",
            columns: [
              {
                label: "",
                fields: [
                  {
                    fieldname: "_crispy_image",
                    fieldtype: "Data",
                    label: "Crispy Image",
                    crispy_image: "seal.svg",
                  },
                ],
              },
            ],
          },
        ],
      },
      null,
      "Sales Invoice",
      { name: "INV-1" },
      {},
    );

    expect(typst).toContain('#crispy_image("seal.svg", width: 100%)');
    expect(typst).not.toContain("#doc._crispy_image");
  });

  it("renders Crispy Image sizing settings", () => {
    const typst = translateJSONToTypst(
      {
        sections: [
          {
            label: "",
            columns: [
              {
                label: "",
                fields: [
                  {
                    fieldname: "_crispy_image",
                    fieldtype: "Crispy Image",
                    label: "Crispy Image",
                    crispy_image: "logo.svg",
                    crispy_image_width: "28.5mm",
                    crispy_image_height: "12mm",
                    crispy_image_fit: "contain",
                  },
                ],
              },
            ],
          },
        ],
      },
      null,
      "Sales Invoice",
      { name: "INV-1" },
      {},
    );

    expect(typst).toContain(
      '#crispy_image("logo.svg", width: 28.5mm, height: 12mm, fit: "contain")',
    );
    expect(typst).not.toContain("#place(");
  });

  it("keeps leading comments inside multiline Crispy Typst Block cells", () => {
    const typst = translateJSONToTypst(
      {
        sections: [
          {
            label: "",
            columns: [
              {
                label: "",
                fields: [
                  {
                    fieldname: "_crispy_typst_block",
                    fieldtype: "Crispy Typst Block",
                    label: "Crispy Typst Block",
                    crispy_typst_block: "invoice_heading",
                    crispy_typst_block_code: `// DocType Heading
#grid(
  columns: (1fr, 1fr),
  [#doc.doctype],
  [#doc.name]
)`,
                  },
                ],
              },
            ],
          },
        ],
      },
      null,
      "Sales Invoice",
      { name: "INV-1" },
      {},
    );

    expect(typst).toMatch(/\[\n\s*\/\/ DocType Heading\n\s*#grid\(/);
    expect(typst).toMatch(/\)\n\s*\],/);
    expect(typst).not.toContain("[, // DocType Heading");
  });

  it("renders a placeholder for unresolved Crispy Typst Blocks", () => {
    const typst = translateJSONToTypst(
      {
        sections: [
          {
            label: "",
            columns: [
              {
                label: "",
                fields: [
                  {
                    fieldname: "_crispy_typst_block",
                    fieldtype: "Crispy Typst Block",
                    label: "Crispy Typst Block",
                    crispy_typst_block: "missing_block",
                  },
                ],
              },
            ],
          },
        ],
      },
      null,
      "Sales Invoice",
      { name: "INV-1" },
      {},
    );

    expect(typst).toContain("Missing Crispy Typst Block: missing_block");
  });
});
