import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CrispyTemplatePublishDialog from "../../components/CrispyTemplatePublishDialog.vue";

describe("template publication history", () => {
  it("shows active/retired versions, notes, and immutable snapshot hashes", () => {
    const wrapper = mount(CrispyTemplatePublishDialog, {
      props: {
        open: true,
        loading: false,
        publishing: false,
        preview: {
          template_name: "invoice-acme-v1.2",
          template_id: "invoice-acme-v1.2",
          company: "ACME",
          next_version: "1.2",
          current_version: "1.1",
          version_bump: "minor",
          snapshot_hash: "a".repeat(64),
          history: [
            {
              name: "invoice-acme-v1.1",
              version: "1.1",
              status: "Approved",
              is_active: 1,
              notes: "Current approval",
              snapshot_hash: "b".repeat(64),
            },
            {
              name: "invoice-acme-v1.0",
              version: "1.0",
              status: "Superseded",
              is_active: 0,
              notes: "Initial approval",
              snapshot_hash: "c".repeat(64),
            },
          ],
        },
      },
    });

    expect(wrapper.text()).toContain("Template history");
    expect(wrapper.text()).toContain("Current approval");
    expect(wrapper.text()).toContain("Superseded");
    expect(wrapper.findAll(".template-publish__history-row")).toHaveLength(2);
    expect(
      wrapper.find(".template-publish__history-row code").attributes("title"),
    ).toBe("b".repeat(64));
  });
});
