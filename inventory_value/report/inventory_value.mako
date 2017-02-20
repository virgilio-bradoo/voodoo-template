## -*- coding: utf-8 -*-
<html>
<head>
     <style type="text/css">
        ${css}

.list_main_table {
border:thin solid #E3E4EA;
text-align:center;
border-collapse: collapse;
}
table.list_main_table {
    margin-top: 20px;
}
.list_main_headers {
    padding: 0;
}
.list_main_headers th {
    border: thin solid #000000;
    padding-right:3px;
    padding-left:3px;
    background-color: #EEEEEE;
    text-align:center;
    font-size:12;
    font-weight:bold;
}
.list_main_table td {
    padding-right:3px;
    padding-left:3px;
    padding-top:3px;
    padding-bottom:3px;
}
.list_main_lines,
.list_main_footers {
    padding: 0;
}
.list_main_footers {
    padding-top: 15px;
}
.list_main_lines td,
.list_main_lines tr {
    padding-top: 10px;
}
.list_main_footers td,
.list_main_footers th {
    text-align:left;
    font-size:12;
}

.list_main_lines td {
    border-bottom:thin solid #EEEEEE
}

.list_main_footers td {
    border: thin solid  #ffffff;
}

.list_main_footers th {
    text-align:right;
}

td .total_empty_cell {
    width: 77%;
}
td .total_sum_cell {
    width: 13%;
}

tfoot.totals tr:first-child td{
    padding-top: 15px;
}

.nobreak {
    page-break-inside: avoid;
}
caption.formatted_note {
    text-align:left;
    border-right:thin solid #EEEEEE;
    border-left:thin solid #EEEEEE;
    border-top:thin solid #EEEEEE;
    padding-left:10px;
    font-size:11;
    caption-side: bottom;
}
caption.formatted_note p {
    margin: 0;
}
.list_bank_table {
    text-align:center;
    border-collapse: collapse;
    page-break-inside: avoid;
    display:table;
}

.act_as_row {
   display:table-row;
}
.list_bank_table .act_as_thead {
    background-color: #EEEEEE;
    text-align:left;
    font-size:12;
    font-weight:bold;
    padding-right:3px;
    padding-left:3px;
    white-space:nowrap;
    background-clip:border-box;
    display:table-cell;
}
.list_bank_table .act_as_cell {
    text-align:left;
    font-size:12;
    padding-right:3px;
    padding-left:3px;
    padding-top:3px;
    padding-bottom:3px;
    white-space:nowrap;
    display:table-cell;
}


.list_tax_table {
}
.list_tax_table td {
    text-align:left;
    font-size:12;
}
.list_tax_table th {
}
.list_tax_table thead {
    display:table-header-group;
}


.list_total_table {
    border:thin solid #E3E4EA;
    text-align:center;
    border-collapse: collapse;
}
.list_total_table td {
    border-top : thin solid #EEEEEE;
    text-align:left;
    font-size:12;
    padding-right:3px;
    padding-left:3px;
    padding-top:3px;
    padding-bottom:3px;
}
.list_total_table th {
    background-color: #EEEEEE;
    border: thin solid #000000;
    text-align:center;
    font-size:12;
    font-weight:bold;
    padding-right:3px
    padding-left:3px
}
.list_total_table thead {
    display:table-header-group;
}

.right_table {
    right: 4cm;
    width:"100%";
}

.std_text {
    font-size:12;
}


td.amount, th.amount {
    text-align: right;
    white-space: nowrap;
}

td.date {
    white-space: nowrap;
    width: 90px;
}

td.vat {
    white-space: nowrap;
}

.address .invoice {
    font-size: 12px;
    width: 150px;
    float: left;
}

.address .shipping {
    font-size: 12px;
    width: 185px;
    float: left;
    margin-left: 75px
}

.address .recipient {
    font-size: 12px;
    width: 150px;
    margin-left: 350px;
    margin-right: 60px;
    float: right;
}

.main_col1 {
    width: 45%;
}
td.main_col1 {
    text-align:left;
    vertical-align:top;
}
.main_col2 {
    width: 10%;
    vertical-align:top;
}
.main_col3 {
    width: 10%;
    text-align:center;
    vertical-align:top;
}
.main_col6 {
    width: 15%;
    vertical-align:top;
}
.main_col4 {
    width: 10%;
    text-align:center;
    vertical-align:top;
}
.main_col5 {
    width: 10%;
    text-align:center;
    vertical-align:top;
}
    </style>

</head>
<body>
    <%page expression_filter="entity"/>

    %for inv in objects :
        <table class="list_main_table" width="100%" >
            <thead>
                <tr>
	          <th class="list_main_headers" style="width: 100%">
	            <table style="width:100%">
	              <tr>
                    <th class="main_col1">${_("Produit")}</th>
                    <th class="main_col2">${_("Référence")}</th>
                    <th class="main_col3">${_("Qté")}</th>
                    <th class="main_col4">${_("Immediately Usable")}</th>
                    <th class="main_col5">${_("Prix de revient")}</th>
                    <th class="main_col6">${_("Fournisseur")}</th>
                  </tr>
                </table>
              </th>
                </tr>
            </thead>
            <tbody>
            %for line in inv.inventory_line_ids :
            <tr>
                <td class="list_main_lines" style="width: 100%">
                <div class="nobreak">
                    <table style="width:100%">
              <tr class="line list_main_lines">
                <td class="main_col1">${line.product_id.name or '' | n}</td>
                <td style="text-align:center" class="main_col2">${line.default_code or '' | n}</td>
                <td class="main_col3">${formatLang(line.quantity or 0.0)}</td>
                <td class="main_col4">${formatLang(line.immediatly_usable or 0.0)}</td>
                <td class="main_col5">${formatLang(line.standard_price, digits=get_digits(dp='Account'))}</td>
                <td class="main_col6">${line.supplier_id.name or '' | n}</td>
              </tr>
                 </table>
              </div>
            </td>
          </tr>
           %endfor
            </tbody>
    </table>
        <p style="page-break-after:always"/>
        <br/>
    %endfor
</body>
</html>
