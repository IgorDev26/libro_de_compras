from odoo import fields, models
from odoo.exceptions import ValidationError
from io import BytesIO, StringIO
import xlsxwriter
import xlwt
import base64

class Resumen(models.Model):
    _name = "libro.resumen.ventas"

    f_inicio = fields.Date("Fecha de inicio", required=True)
    f_fin = fields.Date("Fecha final", required=True)
    no_grabadas = fields.Float("Total ventas internas no gravadas", readonly=True)
    importacion_resumen = fields.Float("Total ventas de importacion", readonly=True)
    alicuota_general = fields.Float("Total ventas internas gravadas por alicuota general", readonly=True)
    alicuota_general_mas = fields.Float("Total ventas internas gravadas por alicuota general mas adicional", readonly=True)
    alicuota_reducida = fields.Float("Total ventas internas gravadas por alicuota reducida", readonly=True)
    lines_r = fields.Many2many(comodel_name="libro.ventas", readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],default='choose')
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    name = fields.Char('File Name', size=60)

    def update_resume(self):
        if self.f_inicio <= self.f_fin:
            if self['lines_r']:
                self['lines_r'] = [(5,0,0)]

            data = self.env['libro.ventas'].search([("fecha",">=",self.f_inicio), ("fecha","<=",self.f_fin)])
            total_ventas = 0
            ventas_exentas = 0
            afectas_base = 0
            afectas_impto = 0
            impuesto_ret = 0
            importacion = 0
            alicuota_gen = 0
            alicuota_gen_mas = 0
            alicuota_gen_reducida = 0


            for item in data:
                total_ventas += item['total_ventas']
                ventas_exentas += item['ventas_exentas']
                afectas_base += item['afectas_base']
                afectas_impto += item['afectas_impto']
                impuesto_ret += item['impuesto_ret']
                self['lines_r'] = [(4,item['id'])]

                if item['importacion'] == "si":
                    importacion += item['total_ventas']
                
                if item['afectas_porcent'] == "16":
                    alicuota_gen += item['afectas_impto']
                
                if item['afectas_porcent_no'] == "16":
                    alicuota_gen += item['afectas_impto_no']

                if item['afectas_porcent'] == "24":
                    alicuota_gen_mas += item['afectas_impto']
                
                if item['afectas_porcent_no'] == "24":
                    alicuota_gen_mas += item['afectas_impto_no']

                if item['afectas_porcent'] == "8":
                    alicuota_gen_reducida += item['afectas_impto']
                
                if item['afectas_porcent_no'] == "8":
                    alicuota_gen_reducida += item['afectas_impto_no']
                                
            
            self['importacion_resumen'] = importacion
            self['no_grabadas'] = ventas_exentas
            self['alicuota_general'] = alicuota_gen
            self['alicuota_general_mas'] = alicuota_gen_mas
            self['alicuota_reducida'] = alicuota_gen_reducida
        else:
            raise ValidationError("La fecha inicial no debe ser mayor a la final")
        
    def generate_pdf(self):
        if not self.lines_r:
            raise ValidationError("Por favor actualiza el resume antes de generarlo")
        
        result = []

        for s in self.lines_r:
            result.append({
                "fecha":s['fecha'],
                "numero_factura":s['numero_factura'],
                "importacion":s['importacion'],
                "nota_credito":s['nota_credito'],
                "nota_debito":s['nota_debito'],
                "numero_z":s['numero_z'],
                "numero_mh":s['numero_mh'],
                "nombre_vendedor":s['nombre_vendedor'],
                "estado":s['estado'],
                "r_s_rif":s['r_s_rif'],
                "total_ventas":s['total_ventas'],
                "ventas_exentas":s['ventas_exentas'],
                "afectas_base":s['afectas_base'],
                "afectas_porcent":s['afectas_porcent'],
                "afectas_impto":s['afectas_impto'],
                "afectas_base_no":s['afectas_base_no'],
                "afectas_porcent_no":s['afectas_porcent_no'],
                "afectas_impto_no":s['afectas_impto_no'],
                "impuesto_ret":s['impuesto_ret'],
                "comprobante":s['comprobante'],
                "doc_afectado":s['doc_afectado']
            })

        data = {
            'model':'libro.compras.wizard',
            'ventas':result
        }

        record = self.env['libro.ventas'].search([("id","=",self.id)])
        record.unlink()

        return self.env.ref('libro_de_compras.libro_de_ventas_pdf_report').report_action(self, data=data)

    def generate_xlsx(self):
        if not self.lines_r:
            raise ValidationError("Por favor actualiza el resumen antes de generarlo")

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Resumen Libro de Ventas')
        fp = BytesIO()
    
        bold_font = xlwt.easyxf("font:bold 1, height 250; borders: top dashed, bottom dashed, left dashed, right dashed;")
        bold_center = xlwt.easyxf("font:bold 1, height 250; align: horiz center; borders: top dashed, bottom dashed, left dashed, right dashed; align:vert center;")
        head_style = xlwt.easyxf("font: bold 1; align:horiz center; align:vert center; alignment: wrap True; borders: top dashed, bottom dashed, left dashed, right dashed;")
        value_style = xlwt.easyxf("align: horiz right; font:height 200; borders: bottom dashed, bottom_color white,left dashed, left_color white,right dashed")
        total_style = xlwt.easyxf("borders:top dashed, bottom dashed, left dashed, right dashed")
        result_line = xlwt.easyxf("borders: bottom dashed, bottom_color white,left dashed, left_color white,right dashed")

        ws.write_merge(0,0,0,13,"EMPRESA: " + self.env.user.company_id.name.upper(),bold_font)
        ws.write_merge(0,0,14,29, "RIF:J-854968-6",bold_font)
        ws.write_merge(1,1,0,16,"LIBRO DE VENTAS",bold_center)
        ws.write_merge(1,1,17,29," ",bold_center)
        ws.write_merge(2,2,0,16,"COMPRAS CORRESPONDIENTES DEL " + str(self.lines_r[0]['fecha']) + " AL " + str(self.lines_r[len(self.lines_r) - 1]['fecha']),bold_center)
        ws.write_merge(2,2,17,29," ",bold_center)
        ws.write_merge(3,4,0,13, "IDENTIFICACIÓN DE FACTURA",bold_center)
        ws.write_merge(3,4,14,17, " ",bold_center)
        ws.write_merge(3,4,18,23,"Ventas afectas(Debito Fiscal)",bold_center)
        ws.write_merge(3,4,24,29, " ",bold_center)

        total_ventas = 0
        ventas_exentas = 0
        afectas_base = 0
        afectas_impto = 0
        afectas_base_no = 0
        afectas_impto_no = 0
        impuesto_ret = 0
        importacion = 0
        alicuota_gen = 0
        alicuota_gen_mas = 0
        alicuota_gen_reducida = 0

        row = 4
        col = 0

        excel_lines = ["Fecha", "Número de factura", "Reporte Z Número",
        "Regístro Número MH", "Nombre del vendedor","Estado", "R.Social Rif","Total ventas\n(incluye iva)","Ventas exentas"]

        for head in excel_lines:
            ws.write_merge(5,6,col,col + 1,head,head_style)
            col += 2
        
        ws.write_merge(5,5,18,20,"A contribuyentes",head_style)
        ws.write_merge(5,5,21,23,"A no contribuyentes",head_style)

        ws.write_merge(6,6,18,18,"Base",head_style)
        ws.write_merge(6,6,19,19,"%",head_style)
        ws.write_merge(6,6,20,20,"Impto.",head_style)
        
        ws.write_merge(6,6,21,21,"Base",head_style)
        ws.write_merge(6,6,22,22,"%",head_style)
        ws.write_merge(6,6,23,23,"Impto.",head_style)

        excel_lines = ["Impuesto retenido", "Número de comprobante", "Documento afectado"]
        col = 24

        for head in excel_lines:
            ws.write_merge(5,6,col,col + 1,head,head_style)
            col += 2
        
        row = 7
        for item in self.lines_r:
            if item['importacion'] == "si":
                importacion += item['total_ventas']
            
            if item['afectas_porcent'] == "16":
                alicuota_gen += item['afectas_impto']
            
            if item['afectas_porcent_no'] == "16":
                alicuota_gen += item['afectas_impto_no']

            if item['afectas_porcent'] == "24":
                alicuota_gen_mas += item['afectas_impto']
            
            if item['afectas_porcent_no'] == "24":
                alicuota_gen_mas += item['afectas_impto_no']

            if item['afectas_porcent'] == "8":
                alicuota_gen_reducida += item['afectas_impto']
            
            if item['afectas_porcent_no'] == "8":
                alicuota_gen_reducida += item['afectas_impto_no']
            
            total_ventas += item['total_ventas']
            ventas_exentas += item['ventas_exentas']
            
            afectas_base += item['afectas_base']
            afectas_impto += item['afectas_impto']

            afectas_base_no += item['afectas_base_no']
            afectas_impto_no += item['afectas_impto_no']

            impuesto_ret += item['impuesto_ret']


            ws.write_merge(row,row,0,1,str(item['fecha']),value_style)
            ws.write_merge(row,row,2,3,item['numero_factura'],value_style)
            ws.write_merge(row,row,4,5,item['numero_z'],value_style)
            ws.write_merge(row,row,6,7,item['numero_mh'],value_style)
            ws.write_merge(row,row,8,9,item['nombre_vendedor'],value_style)
            ws.write_merge(row,row,10,11,item['estado'],value_style)
            ws.write_merge(row,row,12,13,item['r_s_rif'],value_style)
            ws.write_merge(row,row,14,15,item['total_ventas'],value_style)
            ws.write_merge(row,row,16,17,item['ventas_exentas'],value_style)
            ws.write_merge(row,row,18,18,item['afectas_base'],value_style)
            ws.write_merge(row,row,19,19,item['afectas_porcent'],value_style)
            ws.write_merge(row,row,20,20,item['afectas_impto'],value_style)
            ws.write_merge(row,row,21,21,item['afectas_base_no'],value_style)
            ws.write_merge(row,row,22,22,item['afectas_porcent_no'],value_style)
            ws.write_merge(row,row,23,23,item['afectas_impto_no'],value_style)
            ws.write_merge(row,row,24,25,item['impuesto_ret'],value_style)
            ws.write_merge(row,row,26,27,item['comprobante'],value_style)
            ws.write_merge(row,row,28,29,item['doc_afectado'],value_style)
            row += 1

        ws.write_merge(row,row,10,13,"Totales afectos a tasa general: ",bold_center)
        ws.write_merge(row,row,0,9," ",bold_center)
        ws.write_merge(row,row,14,15,total_ventas,total_style)
        ws.write_merge(row,row,16,17,ventas_exentas,total_style)
        ws.write_merge(row,row,18,18,afectas_base,total_style)
        ws.write_merge(row,row,19,19," ",total_style)
        ws.write_merge(row,row,20,20,afectas_impto,total_style)
        ws.write_merge(row,row,21,21,afectas_base_no,total_style)
        ws.write_merge(row,row,22,22," ",total_style)
        ws.write_merge(row,row,23,23,afectas_impto_no,total_style)
        ws.write_merge(row,row,24,25,impuesto_ret,total_style)
        ws.write_merge(row,row,26,29," ",total_style)


        row += 1
        ws.write_merge(row,row,0,5,"RESUMEN",bold_font)
        row += 1
        ws.write_merge(row,row,0,5,"Total ventas internas no gravadas: " + str(round(ventas_exentas,2)),result_line)
        row += 1
        ws.write_merge(row,row,0,5,"Total ventas de importación: " + str(round(total_ventas,2)),result_line)
        row += 1
        ws.write_merge(row,row,0,5,"Total ventas internas gravadas por alicuota general: " + str(round(alicuota_gen,2)),result_line)
        row += 1
        ws.write_merge(row,row,0,5,"Total ventas internas gravadas por alicuota general mas adicional: " + str(round(alicuota_gen_mas,2)),result_line)
        row += 1
        ws.write_merge(row,row,0,5,"Total ventas internas gravadas por alicuota reducida: " + str(round(alicuota_gen_reducida,2)),
        xlwt.easyxf("borders: bottom dashed,left dashed, left_color white,right dashed"))

        wb.save(fp)
        out = base64.encodestring(fp.getvalue())
        self.write({'state': 'get', 'report': out, 'name':'Libro de Ventas.xls'})

        return{
            'type' : 'ir.actions.act_url','url':
            'web/content/?model=libro.resumen.ventas&field=report&download=true&id=%s&filename=%s'%(self.id,self.name),
            'target': 'new',
            }