odoo.define('ecosoft_mrp.mrp_bom_report', function(require) {
"use strict";

var core = require('web.core');
var framework = require('web.framework');
var MrpBomReport = require('mrp.mrp_bom_report');

var QWeb = core.qweb;
var _t = core._t;

var MrpBomReportCausa = MrpBomReport.extend({

    get_externos: function(event) {
      var self = this;
      var $parent = $(event.currentTarget).closest('tr');
      var activeID = $parent.data('bom-id');
      var qty = $parent.data('qty');
      var level = $parent.data('level') || 0;
      return this._rpc({
              model: 'report.mrp.report_bom_structure',
              method: 'get_externos',
              args: [
                  activeID,
                  parseFloat(qty),
                  level + 1
              ]
          })
          .then(function (result) {
              self.render_html(event, $parent, result);
          });
    },
    
});

core.action_registry.add('mrp_bom_report', MrpBomReportCausa);
return MrpBomReportCausa;

});
