 de fecha."""
        parser = CSVGenericParser()
        
        assert parser.parse_date("15/01/2024") == date(2024, 1, 15)
        assert parser.parse_date("15-01-2024") == date(2024, 1, 15)
        assert parser.parse_date("2024-01-15") == date(2024, 1, 15)
        assert parser.parse_date("15.01.2024") == date(2024, 1, 15)
    
    def test_transaction_hash(self):
        """Test que el hash es consistente y único."""
        tx1 = TransaccionRaw(
            fecha=date(2024, 1, 15),
            concepto="Pago alquiler",
            importe=Decimal("-1500.00"),
        )
        tx2 = TransaccionRaw(
            fecha=date(2024, 1, 15),
            concepto="Pago alquiler",
            importe=Decimal("-1500.00"),
        )
        tx3 = TransaccionRaw(
            fecha=date(2024, 1, 16),
            concepto="Pago alquiler",
            importe=Decimal("-1500.00"),
        )
        
        # Mismo contenido = mismo hash
        assert tx1.compute_hash() == tx2.compute_hash()
        
        # Diferente fecha = diferente hash
        assert tx1.compute_hash() != tx3.compute_hash()


class TestOFXParser:
    """Tests para OFXParser."""
    
    def test_detect_ofx(self):
        """Test detección de formato OFX."""
        from app.services.parsers import OFXParser
        
        parser = OFXParser()
        
        ofx_content = b"OFXHEADER:100\nDATA:OFXSGML"
        assert parser.detect(ofx_content)
        
        csv_content = b"Fecha;Concepto;Importe"
        assert not parser.detect(csv_content)
