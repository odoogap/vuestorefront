/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { WebsitePreview } from '@website/client_actions/website_preview/website_preview';
import { _t } from "@web/core/l10n/translation";
import wUtils from '@website/js/utils';
import { useService, useBus } from '@web/core/utils/hooks';
import { unslugHtmlDataObject } from '@website/services/website_service';
import {OptimizeSEODialog} from '@website/components/dialog/seo';
import { WebsiteDialog } from "@website/components/dialog/dialog";
import { SIZES, utils as uiUtils } from "@web/core/ui/ui_service";

const { onWillStart, onMounted, onWillUnmount, useRef, useEffect, useState, useExternalListener } = owl;

// overwrite to avoid redirect on website domain
patch(WebsitePreview.prototype, {
    setup() {
        this.websiteService = useService('website');
        this.dialogService = useService('dialog');
        this.title = useService('title');
        this.user = useService('user');
        this.router = useService('router');
        this.action = useService('action');
        this.orm = useService('orm');

        this.iframeFallbackUrl = '/website/iframefallback';

        this.iframe = useRef('iframe');
        this.iframefallback = useRef('iframefallback');
        this.container = useRef('container');
        this.websiteContext = useState(this.websiteService.context);
        this.blockedState = useState({
            isBlocked: false,
            showLoader: false,
        });
        // The params used to configure the context should be ignored when the
        // action is restored (example: click on the breadcrumb).
        this.isRestored = this.props.action.jsId === this.websiteService.actionJsId;
        this.websiteService.actionJsId = this.props.action.jsId;

        useBus(this.websiteService.bus, 'BLOCK', (event) => this.block(event.detail));
        useBus(this.websiteService.bus, 'UNBLOCK', () => this.unblock());
        useExternalListener(window, "keydown", this._onKeydownRefresh.bind(this));

        onWillStart(async () => {
            const [backendWebsiteRepr] = await Promise.all([
                this.orm.call('website', 'get_current_website'),
                this.websiteService.fetchWebsites(),
                this.websiteService.fetchUserGroups(),
            ]);
            this.backendWebsiteId = unslugHtmlDataObject(backendWebsiteRepr).id;

            const encodedPath = encodeURIComponent(this.path);
            if (this.websiteDomain && !wUtils.isHTTPSorNakedDomainRedirection(this.websiteDomain, window.location.origin)) {
                // The website domain might be the naked one while the naked one
                // is actually redirecting to `www` (or the other way around).
                // In such a case, we need to consider those 2 from the same
                // domain and let the iframe load that "different" domain. The
                // iframe will actually redirect to the correct one (naked/www),
                // which will ends up with the same domain as the parent window
                // URL (event if it wasn't, it wouldn't be an issue as those are
                // really considered as the same domain, the user will share the
                // same session and CORS errors won't be a thing in such a case)
                this.dialogService.add(WebsiteDialog, {
                    title: _t("Redirecting..."),
                    body: _t("You are about to be redirected to the domain configured for your website ( %s ). This is necessary to edit or view your website from the Website app. You might need to log back in.", this.websiteDomain),
                    showSecondaryButton: false,
                }, {
                    onClose: () => {
                        window.location.href = `${encodeURI(this.websiteDomain)}`;
                    }
                });
            } else {
                this.initialUrl = `/website/force/${encodeURIComponent(this.websiteId)}?path=${encodedPath}`;
            }
        });
        useEffect(() => {
            this.websiteService.currentWebsiteId = this.websiteId;
            if (this.isRestored) {
                return;
            }

            const isScreenLargeEnoughForEdit =
                uiUtils.getSize() >= SIZES.MD;
            if (!isScreenLargeEnoughForEdit && this.props.action.context.params) {
                this.props.action.context.params.enable_editor = false;
                this.props.action.context.params.with_loader = false;
            }

            this.websiteService.context.showNewContentModal = this.props.action.context.params && this.props.action.context.params.display_new_content;
            this.websiteService.context.edition = this.props.action.context.params && !!this.props.action.context.params.enable_editor;
            this.websiteService.context.translation = this.props.action.context.params && !!this.props.action.context.params.edit_translations;
            if (this.props.action.context.params && this.props.action.context.params.enable_seo) {
                this.iframe.el.addEventListener('load', () => {
                    this.websiteService.pageDocument = this.iframe.el.contentDocument;
                    this.dialogService.add(OptimizeSEODialog);
                }, {once: true});
            }
            if (this.props.action.context.params && this.props.action.context.params.with_loader) {
                this.websiteService.showLoader({ showTips: true });
            }
        }, () => [this.props.action.context.params]);

        useEffect(() => {
            this.websiteContext.showResourceEditor = false;
        }, () => [
            this.websiteContext.showNewContentModal,
            this.websiteContext.edition,
            this.websiteContext.translation,
        ]);

        onMounted(() => {
            this.websiteService.blockPreview(true, 'load-iframe');
            this.iframe.el.addEventListener('load', () => this.websiteService.unblockPreview('load-iframe'), { once: true });
            // For a frontend page, it is better to use the
            // OdooFrameContentLoaded event to unblock the iframe, as it is
            // triggered faster than the load event.
            this.iframe.el.addEventListener('OdooFrameContentLoaded', () => this.websiteService.unblockPreview('load-iframe'), { once: true });
        });

        onWillUnmount(() => {
            this.websiteService.context.showResourceEditor = false;
            const { pathname, search, hash } = this.iframe.el.contentWindow.location;
            this.websiteService.lastUrl = `${pathname}${search}${hash}`;
            this.websiteService.currentWebsiteId = null;
            this.websiteService.websiteRootInstance = undefined;
            this.websiteService.pageDocument = null;
        });

        /**
         * This removes the 'Odoo' prefix of the title service to display
         * cleanly the frontend's document title (see _replaceBrowserUrl), and
         * replaces the backend favicon with the frontend's one.
         * These changes are reverted when the component is unmounted.
         */
        useEffect(() => {
            const backendIconEl = document.querySelector("link[rel~='icon']");
            // Save initial backend values.
            const backendIconHref = backendIconEl.href;
            const { zopenerp } = this.title.getParts();
            this.iframe.el.addEventListener('load', () => {
                // Replace backend values with frontend's ones.
                this.title.setParts({ zopenerp: null });
                const frontendIconEl = this.iframe.el.contentDocument.querySelector("link[rel~='icon']");
                if (frontendIconEl) {
                    backendIconEl.href = frontendIconEl.href;
                }
            }, { once: true });
            return () => {
                // Restore backend initial values when leaving.
                this.title.setParts({ zopenerp, action: null });
                backendIconEl.href = backendIconHref;
            };
        }, () => []);

        useEffect(() => {
            let leftOnBackNavigation = false;
            // When reaching a "regular" url of the webclient's router, an
            // hashchange event should be dispatched to properly display the
            // content of the previous URL before reaching the client action,
            // which was lost after being replaced for the frontend's URL.
            const handleBackNavigation = () => {
                if (window.location.pathname === '/web') {
                    window.dispatchEvent(new HashChangeEvent('hashchange', {
                        newURL: window.location.href.toString()
                    }));
                    leftOnBackNavigation = true;
                }
            };
            window.addEventListener('popstate', handleBackNavigation);
            return () => {
                window.removeEventListener('popstate', handleBackNavigation);
                // When leaving the client action, its original url is pushed
                // so that the router can replay the action on back navigation
                // from other screens.
                if (!leftOnBackNavigation) {
                    history.pushState({}, null, this.backendUrl);
                }
            };
        }, () => []);

        const toggleIsMobile = () => {
            const wrapwrapEl = this.iframe.el.contentDocument.querySelector('#wrapwrap');
            if (wrapwrapEl) {
                wrapwrapEl.classList.toggle('o_is_mobile', this.websiteContext.isMobile);
            }
        };
        // Toggle the 'o_is_mobile' class on the wrapwrap when 'isMobile'
        // changes in the context. (e.g. Click on mobile preview buttons)
        useEffect(toggleIsMobile, () => [this.websiteContext.isMobile]);

        // Toggle the 'o_is_mobile' class on the wrapwrap according to
        // 'isMobile' on iframe load.
        useEffect(() => {
            this.iframe.el.addEventListener('OdooFrameContentLoaded', toggleIsMobile);
            return () => this.iframe.el.removeEventListener('OdooFrameContentLoaded', toggleIsMobile);
        }, () => []);
    }
});
