## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
        ${css}
    </style>
</head>

<body>
    <%page expression_filter="entity"/>
    <%
    def carriage_returns(text):
        return text.replace('\n', '<br />')
    %>
    %for picking in objects:
        <% setLang(picking.partner_id.lang) %>
        <div class="address">
            <table class="invoice">
                %if picking.partner_id.parent_id:
                <tr><td class="name">${picking.partner_id.parent_id.name or ''}</td></tr>
                <tr><td>${picking.partner_id.title and picking.partner_id.title.name or ''} ${picking.partner_id.name }</td></tr>
                <% address_lines = picking.partner_id.contact_address.split("\n")[1:] %>
                %else:
                <tr><td class="name">${picking.partner_id.title and picking.partner_id.title.name or ''} ${picking.partner_id.name }</td></tr>
                <% address_lines = picking.partner_id.contact_address.split("\n") %>
                %endif
                %for part in address_lines:
                    %if part:
                    <tr><td>${part}</td></tr>
                    %endif
                %endfor
            </table>

        </div>
        
        <h1 style="clear:both;">${_(u'Bon de réception') } ${picking.name}</h1>
        
        <table class="basic_table" width="100%">
            <tr>
                <td style="font-weight:bold;">${_("Origin")}</td>
                <td style="font-weight:bold;">${_("Scheduled Date")}</td>
                <td style="font-weight:bold;">${_('Weight')}</td>
                <td style="font-weight:bold;">${_('Delivery Method')}</td>
            </tr>
            <tr>
                <td>${picking.origin or ''}</td>
                <td>${formatLang(picking.date_done, date=True) or formatLang(time.strftime("%Y-%m-%d", time.gmtime()), date=True)}</td>
                <td>${picking.weight}</td>
                <td>${picking.carrier_id and picking.carrier_id.name or ''}</td>
            </tr>
        </table>
    
        <table border=1 frame=void rules=rows class="list_sale_table" width="100%" style="margin-top: 20px;">
          <col width="50%">
          <col width="20%">
          <col width="10%">
          <col width="20%">
            <thead>
                <tr>
                    <th style="text-align:left; ">${_("Description")}</th>
                    <th style="text-align:center; ">${_("Reference")}</th>
                    <th style="text-align:center; ">${_("Geolocation")}</th>
                    <th class="amount">${_("Quantity")}</th>
                </tr>
            </thead>
            <tbody>
            %for line in picking.move_lines:
            %if line.state != 'cancel' :

                <tr class="line">
                    <td style="text-align:left; " >${ line.product_id.description_purchase or ''} </td>
                    <td style="text-align:center; " >${ line.product_id.original_default_code or ''}</td>
                    <td style="text-align:center; " >${ line.product_geolocation or ''}</td>
                    <td class="amount" >${ formatLang(line.product_qty) } ${line.product_uom.name}</td>
                </tr>
            %endif
            %endfor
        </table>
        
        <br/>
        %if picking.note :
            <p class="std_text">${picking.note | carriage_returns}</p>
        %endif

        <p style="page-break-after: always"/>
        <br/>
    %endfor
</body>
</html>
