from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Factura(models.Model):
    _name = "libro.ventas"
    fecha = fields.Date("Fecha")
    estado = fields.Selection([("borrador","Borrador"),("confirmado","Confirmado"),("publicado","Publicado")])
    nota_credito = fields.Char("Nota de crédito")
    nota_debito = fields.Char("Nota de débito")
    numero_factura = fields.Char("Número de factura")
    numero_z = fields.Char("Número Z")
    numero_mh = fields.Char("Número MH")
    nombre_vendedor = fields.Char("Nombre de vendedor")
    r_s_rif = fields.Char("R.Social Rif")
    total_ventas = fields.Float("Total ventas")
    contribuyente = fields.Selection([
    ("si","Si"),
    ("no","No")
    ])
    importacion = fields.Selection([("si","Si"),("no","No")], string="Venta de importación")
    ventas_exentas = fields.Float("Ventas exentas")
    ventas_afectas = fields.Float("Ventas afectas")
    afectas_base = fields.Float("Base de afecta")
    afectas_porcent = fields.Selection([("8","Alicuota reducida"),("16","Alicuota general"),("24","Alicuota más adicional")], string="Porcentaje de afecta", default="16")
    afectas_impto = fields.Float("Impto de afecta")
    afectas_base_no = fields.Float("Base de afecta")
    afectas_porcent_no = fields.Selection([("8","Alicuota reducida"),("16","Alicuota general"),("24","Alicuota más adicional")], string="Porcentaje de afecta", default="16")
    afectas_impto_no = fields.Float("Impto de afecta")
    impuesto_ret = fields.Float("Impuesto retenido")
    comprobante = fields.Char("Número de comprobante")
    doc_afectado = fields.Char("Documento afectado")
    lines_l = fields.Many2many('libro.resumen.ventas', 'libro_compras_libro_resumen_ventas_rel')

    @api.onchange("afectas_base", "afectas_porcent")
    def update_contribuyentes(self):
        self.afectas_impto = (self.afectas_base * int(self.afectas_porcent)) / 100
        self.total_ventas = self.afectas_base + self.afectas_impto + self.afectas_base_no + self.afectas_impto_no

    @api.onchange("afectas_base_no", "afectas_porcent_no")
    def update_no_contribuyentes(self):
        self.afectas_impto_no = (self.afectas_base_no * int(self.afectas_porcent_no)) / 100
        self.total_ventas = self.afectas_base + self.afectas_impto + self.afectas_base_no + self.afectas_impto_no
