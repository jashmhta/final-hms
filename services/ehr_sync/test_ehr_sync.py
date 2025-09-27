"""
Test suite for EHR Synchronization Service
Enterprise-grade testing with real-world scenarios
"""

import asyncio
import json
from datetime import date, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from main import EHRSynchronizationService, EHRSyncRequest, EHRSystemConfig, SyncStatus


class TestEHRSynchronizationService:
    """Test suite for EHR Synchronization Service"""

    @pytest.fixture
    async def ehr_service(self):
        """Create EHR service instance for testing"""
        service = EHRSynchronizationService()
        with patch.object(service, "initialize", return_value=None):
            await service.initialize()
        return service

    @pytest.fixture
    def sample_patient_data(self):
        """Sample patient data for testing"""
        return {
            "id": "PAT001",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-01-15",
            "gender": "M",
            "phone": "+1-555-123-4567",
            "email": "john.doe@example.com",
            "address": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "country": "USA",
            "medical_record_number": "MRN001",
            "ssn": "123-45-6789",
        }

    @pytest.fixture
    def sample_encounter_data(self):
        """Sample encounter data for testing"""
        return {
            "id": "ENC001",
            "patient_id": "PAT001",
            "encounter_type": "OUTPATIENT",
            "start_date": "2024-01-15T10:00:00",
            "end_date": "2024-01-15T10:30:00",
            "provider_id": "PROV001",
            "facility_id": "FAC001",
            "diagnosis": ["Z00.00"],
            "procedures": ["99213"],
        }

    @pytest.fixture
    def sample_ehr_config(self):
        """Sample EHR system configuration"""
        return {
            "name": "Test Epic System",
            "system_type": "EPIC",
            "base_url": "https://test-epic.example.com/api",
            "api_key": "test_api_key_123",
            "sync_direction": "BIDIRECTIONAL",
            "data_format": "FHIR_R4",
            "sync_interval_minutes": 30,
            "timeout_seconds": 30,
        }

    class TestInitialization:
        """Test service initialization"""

        @pytest.mark.asyncio
        async def test_initialize_service(self, ehr_service):
            """Test service initialization"""
            assert ehr_service.db_url is not None
            assert ehr_service.redis_url is not None
            assert ehr_service.encryption_key is None  # Default for testing

        @pytest.mark.asyncio
        async def test_initialize_with_encryption_key(self):
            """Test service initialization with encryption key"""
            with patch.dict(
                "os.environ", {"EHR_ENCRYPTION_KEY": "test-key-for-encryption"}
            ):
                service = EHRSynchronizationService()
                with patch.object(service, "initialize", return_value=None):
                    await service.initialize()
                assert service.encryption_key == "test-key-for-encryption"

    class TestEHRSystemRegistration:
        """Test EHR system registration"""

        @pytest.mark.asyncio
        async def test_register_ehr_system_success(
            self, ehr_service, sample_ehr_config
        ):
            """Test successful EHR system registration"""
            with patch.object(ehr_service, "_test_ehr_connectivity", return_value=True):
                system_id = await ehr_service.register_ehr_system(sample_ehr_config)
                assert system_id is not None
                assert len(system_id) == 36  # UUID format

        @pytest.mark.asyncio
        async def test_register_ehr_system_missing_fields(self, ehr_service):
            """Test EHR system registration with missing required fields"""
            incomplete_config = {
                "name": "Test System"
            }  # Missing system_type and base_url
            with pytest.raises(
                ValueError, match="Required field 'system_type' is missing"
            ):
                await ehr_service.register_ehr_system(incomplete_config)

        @pytest.mark.asyncio
        async def test_register_ehr_system_connectivity_failure(
            self, ehr_service, sample_ehr_config
        ):
            """Test EHR system registration with connectivity failure"""
            with patch.object(
                ehr_service, "_test_ehr_connectivity", return_value=False
            ):
                with pytest.raises(Exception, match="Failed to register EHR system"):
                    await ehr_service.register_ehr_system(sample_ehr_config)

    class TestDataTransformation:
        """Test data transformation"""

        @pytest.mark.asyncio
        async def test_transform_data_no_mappings(
            self, ehr_service, sample_patient_data
        ):
            """Test data transformation with no mappings"""
            ehr_system = Mock()
            ehr_system.id = "test_system_id"

            transformed_data = await ehr_service._transform_data(
                sample_patient_data, ehr_system
            )
            assert transformed_data == sample_patient_data

        @pytest.mark.asyncio
        async def test_apply_transformation_date_format(self, ehr_service):
            """Test date format transformation"""
            rule = {
                "type": "date_format",
                "input_format": "%Y-%m-%d",
                "output_format": "%Y%m%d",
            }

            result = await ehr_service._apply_transformation("2024-01-15", rule)
            assert result == "20240115"

        @pytest.mark.asyncio
        async def test_apply_transformation_code_mapping(self, ehr_service):
            """Test code mapping transformation"""
            rule = {
                "type": "code_mapping",
                "mapping": {"M": "male", "F": "female", "U": "unknown"},
            }

            result = await ehr_service._apply_transformation("M", rule)
            assert result == "male"

        @pytest.mark.asyncio
        async def test_apply_transformation_concatenate(self, ehr_service):
            """Test concatenate transformation"""
            rule = {
                "type": "concatenate",
                "separator": " ",
                "fields": ["first_name", "last_name"],
            }

            data = {"first_name": "John", "last_name": "Doe"}
            result = await ehr_service._apply_transformation(data, rule)
            assert result == "John Doe"

    class TestFHIRConversion:
        """Test FHIR data conversion"""

        @pytest.mark.asyncio
        async def test_convert_to_fhir_patient_basic(
            self, ehr_service, sample_patient_data
        ):
            """Test basic FHIR patient conversion"""
            fhir_patient = await ehr_service._convert_to_fhir_patient(
                sample_patient_data
            )

            assert fhir_patient["resourceType"] == "Patient"
            assert len(fhir_patient["name"]) == 1
            assert fhir_patient["name"][0]["family"] == "Doe"
            assert fhir_patient["name"][0]["given"] == ["John"]
            assert fhir_patient["gender"] == "m"
            assert fhir_patient["birthDate"] == "1980-01-15"

        @pytest.mark.asyncio
        async def test_convert_to_fhir_patient_with_identifiers(
            self, ehr_service, sample_patient_data
        ):
            """Test FHIR patient conversion with identifiers"""
            fhir_patient = await ehr_service._convert_to_fhir_patient(
                sample_patient_data
            )

            assert len(fhir_patient["identifier"]) == 2
            mrn_identifier = next(
                (
                    id
                    for id in fhir_patient["identifier"]
                    if id["system"] == "http://hospital.com/mrn"
                ),
                None,
            )
            assert mrn_identifier is not None
            assert mrn_identifier["value"] == "MRN001"

        @pytest.mark.asyncio
        async def test_convert_to_fhir_patient_with_contact(
            self, ehr_service, sample_patient_data
        ):
            """Test FHIR patient conversion with contact information"""
            fhir_patient = await ehr_service._convert_to_fhir_patient(
                sample_patient_data
            )

            assert len(fhir_patient["telecom"]) == 2
            phone_telecom = next(
                (tel for tel in fhir_patient["telecom"] if tel["system"] == "phone"),
                None,
            )
            assert phone_telecom is not None
            assert phone_telecom["value"] == "+1-555-123-4567"

        @pytest.mark.asyncio
        async def test_convert_to_fhir_patient_with_address(
            self, ehr_service, sample_patient_data
        ):
            """Test FHIR patient conversion with address"""
            fhir_patient = await ehr_service._convert_to_fhir_patient(
                sample_patient_data
            )

            assert len(fhir_patient["address"]) == 1
            address = fhir_patient["address"][0]
            assert address["line"] == ["123 Main St"]
            assert address["city"] == "Anytown"
            assert address["state"] == "CA"
            assert address["postalCode"] == "12345"

    class TestHL7Conversion:
        """Test HL7 data conversion"""

        @pytest.mark.asyncio
        async def test_convert_to_hl7_patient_create(
            self, ehr_service, sample_patient_data
        ):
            """Test HL7 patient conversion for create operation"""
            hl7_message = await ehr_service._convert_to_hl7_patient(
                sample_patient_data, "CREATE"
            )

            assert hl7_message.startswith("MSH|^~\\&|HMS|HOSPITAL")
            assert "ADT^A04" in hl7_message
            assert "PID" in hl7_message
            assert "DOE^JOHN" in hl7_message
            assert "19800115" in hl7_message
            assert "M" in hl7_message

        @pytest.mark.asyncio
        async def test_convert_to_hl7_patient_unsupported_type(
            self, ehr_service, sample_patient_data
        ):
            """Test HL7 patient conversion with unsupported type"""
            hl7_message = await ehr_service._convert_to_hl7_patient(
                sample_patient_data, "UNSUPPORTED"
            )
            assert hl7_message == ""

    class TestEncryption:
        """Test data encryption and decryption"""

        @pytest.mark.asyncio
        async def test_encrypt_sensitive_data(self, ehr_service):
            """Test sensitive data encryption"""
            ehr_service.cipher_suite = Mock()
            ehr_service.cipher_suite.encrypt.return_value = b"encrypted_data"

            config = {
                "name": "Test System",
                "api_key": "secret_key",
                "password": "secret_password",
            }

            encrypted = await ehr_service._encrypt_sensitive_data(config)

            assert encrypted["name"] == "Test System"  # Not encrypted
            assert encrypted["api_key"] == "encrypted_data"
            assert encrypted["password"] == "encrypted_data"

        @pytest.mark.asyncio
        async def test_decrypt_sensitive_data(self, ehr_service):
            """Test sensitive data decryption"""
            ehr_service.cipher_suite = Mock()
            ehr_service.cipher_suite.decrypt.return_value = b"decrypted_data"

            config = {
                "name": "Test System",
                "api_key": "encrypted_data",
                "password": "encrypted_data",
            }

            decrypted = await ehr_service._decrypt_sensitive_data(config)

            assert decrypted["name"] == "Test System"
            assert decrypted["api_key"] == "decrypted_data"
            assert decrypted["password"] == "decrypted_data"

    class TestSynchronization:
        """Test synchronization operations"""

        @pytest.mark.asyncio
        async def test_sync_patient_fhir_success(
            self, ehr_service, sample_patient_data
        ):
            """Test successful FHIR patient synchronization"""
            request = EHRSyncRequest(
                ehr_system_id="test_system",
                sync_type="CREATE",
                entity_type="PATIENT",
                entity_id="PAT001",
                data=sample_patient_data,
            )

            ehr_system = Mock()
            ehr_system.id = "test_system"
            ehr_system.data_format = "FHIR_R4"
            ehr_system.timeout_seconds = 30

            with patch.object(
                ehr_service, "_get_ehr_system", return_value=ehr_system
            ), patch.object(
                ehr_service, "_transform_data", return_value=sample_patient_data
            ), patch.object(
                ehr_service,
                "_get_ehr_headers",
                return_value={"Authorization": "Bearer test"},
            ), patch(
                "aiohttp.ClientSession.post"
            ) as mock_post:

                mock_response = Mock()
                mock_response.status = 201
                mock_response.json = AsyncMock(return_value={"id": "external_id_123"})
                mock_post.return_value.__aenter__.return_value = mock_response

                result = await ehr_service._sync_patient_fhir(
                    request, ehr_system, sample_patient_data
                )

                assert result.status == SyncStatus.COMPLETED
                assert result.external_id == "external_id_123"
                assert result.entity_id == "PAT001"

        @pytest.mark.asyncio
        async def test_sync_patient_hl7_success(self, ehr_service, sample_patient_data):
            """Test successful HL7 patient synchronization"""
            request = EHRSyncRequest(
                ehr_system_id="test_system",
                sync_type="CREATE",
                entity_type="PATIENT",
                entity_id="PAT001",
                data=sample_patient_data,
            )

            ehr_system = Mock()
            ehr_system.id = "test_system"
            ehr_system.data_format = "HL7_V2"
            ehr_system.timeout_seconds = 30

            # Mock HL7 processor
            ehr_service.hl7_processor = Mock()
            ehr_service.hl7_processor.parse_ack = Mock(
                return_value={"acknowledgement_code": "AA"}
            )

            with patch.object(
                ehr_service, "_get_ehr_system", return_value=ehr_system
            ), patch.object(
                ehr_service, "_transform_data", return_value=sample_patient_data
            ), patch.object(
                ehr_service,
                "_get_ehr_headers",
                return_value={"Authorization": "Bearer test"},
            ), patch(
                "aiohttp.ClientSession.post"
            ) as mock_post:

                mock_response = Mock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="MSH|...|")
                mock_post.return_value.__aenter__.return_value = mock_response

                result = await ehr_service._sync_patient_hl7(
                    request, ehr_system, sample_patient_data
                )

                assert result.status == SyncStatus.COMPLETED
                assert result.entity_id == "PAT001"

        @pytest.mark.asyncio
        async def test_sync_patient_unsupported_format(
            self, ehr_service, sample_patient_data
        ):
            """Test patient synchronization with unsupported format"""
            request = EHRSyncRequest(
                ehr_system_id="test_system",
                sync_type="CREATE",
                entity_type="PATIENT",
                entity_id="PAT001",
                data=sample_patient_data,
            )

            ehr_system = Mock()
            ehr_system.id = "test_system"
            ehr_system.data_format = "UNSUPPORTED"

            with pytest.raises(
                ValueError, match="Unsupported data format: UNSUPPORTED"
            ):
                await ehr_service._sync_patient_fhir(
                    request, ehr_system, sample_patient_data
                )

    class TestConnectivity:
        """Test EHR system connectivity"""

        @pytest.mark.asyncio
        async def test_test_ehr_connectivity_success(self, ehr_service):
            """Test successful EHR connectivity check"""
            ehr_system = Mock()
            ehr_system.id = "test_system"
            ehr_system.base_url = "https://test-ehr.example.com"
            ehr_system.api_key = "test_key"

            with patch.object(
                ehr_service,
                "_get_ehr_headers",
                return_value={"Authorization": "Bearer test"},
            ), patch("aiohttp.ClientSession.get") as mock_get:

                mock_response = Mock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await ehr_service._test_ehr_connectivity("test_system")
                assert result is True

        @pytest.mark.asyncio
        async def test_test_ehr_connectivity_failure(self, ehr_service):
            """Test failed EHR connectivity check"""
            ehr_system = Mock()
            ehr_system.id = "test_system"
            ehr_system.base_url = "https://test-ehr.example.com"
            ehr_system.api_key = "test_key"

            with patch.object(
                ehr_service,
                "_get_ehr_headers",
                return_value={"Authorization": "Bearer test"},
            ), patch("aiohttp.ClientSession.get") as mock_get:

                mock_response = Mock()
                mock_response.status = 500
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await ehr_service._test_ehr_connectivity("test_system")
                assert result is False

    class TestMetrics:
        """Test metrics collection"""

        @pytest.mark.asyncio
        async def test_get_sync_metrics(self, ehr_service):
            """Test sync metrics collection"""
            with patch.object(ehr_service, "SessionLocal") as mock_session:
                mock_session.return_value.__aenter__.return_value.query.return_value.filter.return_value.execute.return_value.scalars.return_value.all.return_value = [
                    Mock(status="COMPLETED", processing_time_ms=1000),
                    Mock(status="COMPLETED", processing_time_ms=2000),
                    Mock(status="FAILED", processing_time_ms=500),
                ]

                metrics = await ehr_service.get_sync_metrics(time_range_hours=24)

                assert metrics["total_requests"] == 3
                assert metrics["successful"] == 2
                assert metrics["failed"] == 1
                assert metrics["success_rate"] == 66.66666666666666
                assert metrics["average_processing_time_ms"] == 1166.6666666666667

    class TestWebSockets:
        """Test WebSocket functionality"""

        @pytest.mark.asyncio
        async def test_connect_websocket(self, ehr_service):
            """Test WebSocket connection"""
            websocket = Mock()
            websocket.accept = AsyncMock()
            websocket.send_text = AsyncMock()

            await ehr_service.connect_websocket(websocket, "test_client")

            websocket.accept.assert_called_once()
            assert websocket in ehr_service.active_connections

        @pytest.mark.asyncio
        async def test_broadcast_sync_result(self, ehr_service):
            """Test broadcasting sync result"""
            websocket = Mock()
            websocket.send_text = AsyncMock()
            ehr_service.active_connections = [websocket]

            from main import EHRSyncResponse

            result = EHRSyncResponse(
                request_id="test_request",
                status=SyncStatus.COMPLETED,
                ehr_system_id="test_system",
                entity_type="PATIENT",
                entity_id="PAT001",
            )

            await ehr_service._broadcast_sync_result(result)

            websocket.send_text.assert_called_once()
            call_args = websocket.send_text.call_args[0][0]
            call_data = json.loads(call_args)
            assert call_data["type"] == "sync_result"
            assert call_data["data"]["status"] == "COMPLETED"


# Integration Tests
class TestIntegration:
    """Integration tests for EHR synchronization"""

    @pytest.mark.asyncio
    async def test_full_patient_sync_workflow(
        self, ehr_service, sample_patient_data, sample_ehr_config
    ):
        """Test complete patient synchronization workflow"""
        with patch.object(
            ehr_service, "register_ehr_system", return_value="test_system_id"
        ), patch.object(
            ehr_service, "_get_ehr_system"
        ) as mock_get_system, patch.object(
            ehr_service, "_transform_data", return_value=sample_patient_data
        ), patch.object(
            ehr_service,
            "_get_ehr_headers",
            return_value={"Authorization": "Bearer test"},
        ), patch(
            "aiohttp.ClientSession.post"
        ) as mock_post:

            # Setup EHR system mock
            ehr_system = Mock()
            ehr_system.id = "test_system_id"
            ehr_system.data_format = "FHIR_R4"
            ehr_system.timeout_seconds = 30
            mock_get_system.return_value = ehr_system

            # Setup HTTP response mock
            mock_response = Mock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value={"id": "external_id_123"})
            mock_post.return_value.__aenter__.return_value = mock_response

            # Execute full workflow
            system_id = await ehr_service.register_ehr_system(sample_ehr_config)

            request = EHRSyncRequest(
                ehr_system_id=system_id,
                sync_type="CREATE",
                entity_type="PATIENT",
                entity_id="PAT001",
                data=sample_patient_data,
            )

            result = await ehr_service.sync_patient(request)

            # Verify results
            assert system_id == "test_system_id"
            assert result.status == SyncStatus.COMPLETED
            assert result.external_id == "external_id_123"
            assert result.entity_type == "PATIENT"
            assert result.entity_id == "PAT001"


# Performance Tests
class TestPerformance:
    """Performance tests for EHR synchronization"""

    @pytest.mark.asyncio
    async def test_bulk_patient_sync_performance(
        self, ehr_service, sample_patient_data
    ):
        """Test bulk patient synchronization performance"""
        import time

        # Create multiple patient records
        patients = []
        for i in range(100):
            patient_data = sample_patient_data.copy()
            patient_data["id"] = f"PAT{i:03d}"
            patient_data["medical_record_number"] = f"MRN{i:03d}"
            patients.append(patient_data)

        with patch.object(
            ehr_service, "_get_ehr_system"
        ) as mock_get_system, patch.object(
            ehr_service, "_transform_data", side_effect=lambda x, y: x
        ), patch.object(
            ehr_service,
            "_get_ehr_headers",
            return_value={"Authorization": "Bearer test"},
        ), patch(
            "aiohttp.ClientSession.post"
        ) as mock_post:

            # Setup EHR system mock
            ehr_system = Mock()
            ehr_system.id = "test_system"
            ehr_system.data_format = "FHIR_R4"
            ehr_system.timeout_seconds = 30
            mock_get_system.return_value = ehr_system

            # Setup HTTP response mock
            mock_response = Mock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value={"id": "external_id_123"})
            mock_post.return_value.__aenter__.return_value = mock_response

            # Measure performance
            start_time = time.time()

            tasks = []
            for patient_data in patients:
                request = EHRSyncRequest(
                    ehr_system_id="test_system",
                    sync_type="CREATE",
                    entity_type="PATIENT",
                    entity_id=patient_data["id"],
                    data=patient_data,
                )
                tasks.append(ehr_service.sync_patient(request))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # Verify performance
            total_time = end_time - start_time
            successful_syncs = sum(
                1
                for r in results
                if isinstance(r, type(EHRSyncResponse))
                and r.status == SyncStatus.COMPLETED
            )

            assert successful_syncs == 100
            assert total_time < 30  # Should complete within 30 seconds
            print(
                f"Bulk sync completed in {total_time:.2f} seconds ({successful_syncs/total_time:.2f} syncs/sec)"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
