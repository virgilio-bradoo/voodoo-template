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
.list_main_table th {
    background-color: #EEEEEE;
    border: thin solid #000000;
    text-align:center;
    font-size:12;
    font-weight:bold;
    padding-right:3px;
    padding-left:3px;
}
.list_main_table td {
    border-top : thin solid #EEEEEE;
    text-align:left;
    font-size:12;
    padding-right:3px;
    padding-left:3px;
    padding-top:3px;
    padding-bottom:3px;
}
.list_main_table thead {
    display:table-header-group;
}
div.formatted_note {
    text-align:left;
    padding-left:10px;
    font-size:11;
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
    page-break-inside: avoid;
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
.no_bloc {
    border-top: thin solid  #ffffff ;
}
.right_table {
    right: 4cm;
    width:"100%";
}
.std_text {
    font-size:12;
}
tfoot.totals tr:first-child td{
    padding-top: 15px;
}
th.date {
    width: 90px;
}
td.amount, th.amount {
    text-align: right;
    white-space: nowrap;
}
.header_table {
    text-align: center;
    border: 1px solid lightGrey;
    border-collapse: collapse;
}
.header_table th {
    font-size: 12px;
    border: 1px solid lightGrey;
}
.header_table td {
    font-size: 12px;
    border: 1px solid lightGrey;
}
td.date {
    white-space: nowrap;
    width: 90px;
}
td.vat {
    white-space: nowrap;
}
.address .shipping {
    font-size: 12px;
    float: left;
    width:200px
}
.address .recipient {
    font-size: 12px;
    float: right;
    width:200px
}
.nobreak {
     page-break-inside: avoid;
 }
.align_top {
     vertical-align:text-top;
 }
    </style>
</head>
<body>
    %for inv in objects:
    <h1 style="clear: both; padding-top: 20px;">
        ${inv.name or ''}
    </h1>


    <table class="list_main_table" width="100%" style="margin-top: 20px;">
        <thead>
            <tr>
                <th>Produit</th>
                <th>Référence</th>
                <th>Quantité</th>
                <th>Immediately Usable</th>
                <th>Prix de revient</th>
                <th>Fournisseur</th>
            </tr>
        </thead>
        <tbody>
        %for line in inv.inventory_line_ids :
            <tr>
                <td class="align_top"><div class="nobreak">${line.product_id.name or '' | n}
                </div></td>
                <td class="align_top">${line.default_code or '' | n}</td>
                <td class="amount align_top">${line.quantity or 0.0)}</td>
                <td class="amount align_top">${line.immediatly_usable or 0.0)}</td>
                <td class="amount align_top">${line.standard_price, digits=get_digits(dp='Account')}</td>
                <td class="align_top">${line.default_code or '' | n}</td>
            </tr>
        %endfor
        </tbody>
    </table>
</body>
</html>
