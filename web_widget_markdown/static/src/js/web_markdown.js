/*
Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
*/

odoo.define('web_widget_markdown.markdown', function (require) {
"use strict";

var fieldRegistry = require('web.field_registry');
var basicFields = require('web.basic_fields');
var core = require("web.core");

var _t = core._t;


var markdownField = basicFields.DebouncedField.extend(basicFields.TranslatableFieldMixin, {
    supportedFieldTypes: ['text'],
    template: 'FieldMarkdown',
    jsLibs: [
        '/web_widget_markdown/static/lib/easymde.min.js',
        '/web_widget_markdown/static/lib/marked.min.js',
    ],
    cssLibs: [
        '/web_widget_markdown/static/lib/easymde.min.css'
    ],
    events: {},
    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this.simplemde = {}
    },
    /**
     * When the the widget render, check view mode, if edit we
     * instanciate our EasyMDE
     *
     * @override
     */
    start: function () {
        var self = this;
        if (this.mode === 'edit') {
            var $textarea = this.$el.find('textarea');
            var toolbar = ["bold", "italic", "heading", "|", "quote", "unordered-list", "ordered-list", "|", "link", "image", "|", "preview", "side-by-side", "fullscreen"];
            this.$el.find('span.o_field_translate.btn.btn-link').addClass('d-none');
            // Add translation button inside toolbar
            if (this.field.translate) {
                toolbar.push("|")
                toolbar.push(
                    {
                        name: "translation",
                        action: (editor) => {
                            self._markdownTranslate();
                        },
                        className: "fa fa-globe",
                        title: _t("Translate"),
                    }
                );
            }
            var easyConfig = {
                toolbar: toolbar,
                element: $textarea[0],
                initialValue: this.value,
                uniqueId: "markdown-"+this.model+this.res_id,
                autoRefresh: { delay: 500 },
            }
            if (this.nodeOptions) {
                easyConfig = {...easyConfig, ...this.nodeOptions};
            }
            this.easymde = new EasyMDE(easyConfig);
            this.easymde.codemirror.on("change", this._doDebouncedAction.bind(this));
            this.easymde.codemirror.on("blur", this._doAction.bind(this));
            if (this.field.translate) {
                this.$el = this.$el.add(this._renderTranslateButton());
                this.$el.addClass('o_field_translate');
            }
        }
        return this._super();
    },
    /**
     * return the EasyMDE value
     *
     * @private
     */
    _getValue: function () {
        return this.easymde.value();
    },
    _formatValue: function (value) {
        return this._super.apply(this, arguments) || '';
    },
    _renderEdit: function () {
        this._super.apply(this, arguments);
        var newValue = this._formatValue(this.value);
        if (this.easymde.value() !== newValue) {
            this.easymde.value(newValue);
        }
    },
    _renderReadonly: function () {
        this.$el.html(marked.parse(this._formatValue(this.value)));
    },
    _renderTranslateButton: function () {
        // Remove default odoo translation button
        return $();
    },
    _markdownTranslate: function () {
        this._onTranslate(event);
    },
});

fieldRegistry.add('markdown', markdownField);

return {
    markdownField: markdownField,
};
});
