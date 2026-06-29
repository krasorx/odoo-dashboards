/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class GuidesBrowser extends Component {
    static template = "guides_html_sharing.GuidesBrowser";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            folders: [],
            documents: [],
            selectedDoc: null,
            iframeUrl: "",
        });
        onWillStart(async () => {
            this.state.folders = await this.orm.searchRead(
                "guides.folder", [], ["id", "name", "complete_name", "parent_id"],
                { order: "complete_name" });
            this.state.documents = await this.orm.searchRead(
                "guides.document", [],
                ["id", "name", "folder_id", "version_count"], { order: "name" });
        });
    }

    docsForFolder(folderId) {
        return this.state.documents.filter(
            (d) => d.folder_id && d.folder_id[0] === folderId);
    }

    openDoc(doc) {
        this.state.selectedDoc = doc;
        this.state.iframeUrl = `/guides/render/${doc.id}`;
    }

    openFullscreen() {
        if (this.state.iframeUrl) {
            window.open(this.state.iframeUrl, "_blank");
        }
    }
}

registry.category("actions").add("guides_browser", GuidesBrowser);
