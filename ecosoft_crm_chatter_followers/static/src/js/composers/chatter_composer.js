odoo.define('ecosoft_crm_chatter_followers.composer.Chatter', function (require) {
"use strict";
/**
 * Send to client Checkbox unchecked by default
 *
 */
 
var ChatterComposer = require('mail.composer.Chatter');
    ChatterComposer.include({
        init: function () {
            this._super.apply(this, arguments);
			this.Checked = true;
			// By default Uncheck boxes when sending msg thru chatter if we are in crm.lead
            if (this._model == 'crm.lead') {
                this.Checked = false;
			}
        },		
    });
});
