from odoo import fields, models
from odoo.exceptions import ValidationError
class LibrosWizard(models.TransientModel):
    _name = "libro.compras.wizard"
    f_inicio = fields.Date("Fecha inicio", required=True)
    f_fin = fields.Date("Fecha fin", required=True)

    def generate_pdf(self):
        if self.f_inicio > self.f_fin:
            raise ValidationError("La fecha de inicio es mayor a la fecha final")

        ventas = self.env['libro.compras'].search([("fecha",">=",self.f_inicio),("fecha","<=",self.f_fin)])
        result = []

        for s in ventas:
            result.append({
                "fecha":s['fecha'],
                "numero_factura":s['numero_factura'],
                "nota_credito":s['nota_credito'],
                "nota_debito":s['nota_debito'],
                "numero_z":s['numero_z'],
                "numero_mh":s['numero_mh'],
                "nombre_comprador":s['nombre_comprador'],
                "r_s_rif":s['r_s_rif'],
                "total_compras":s['total_compras'],
                "compras_exentas":s['compras_exentas'],
                "compras_afectas":s['compras_afectas'],
                "contribuyente":s['contribuyente'],
                "impuesto_ret":s['impuesto_ret'],
                "comprobante":s['comprobante'],
                "doc_afectado":s['doc_afectado']
            })

        data = {
            'model':'libro.compras.wizard',
            'form':self.read()[0],
            'ventas':result
        }
        return self.env.ref('libro_de_compras.libro_de_compras_pdf_report').report_action(self, data=data)

    def generate_xlsx(self):
        return 0