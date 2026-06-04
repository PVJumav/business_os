from backend.api.crm.commercial import crud_router
from backend.models.crm import (
    CRMPMOProject,
    CRMSLAAssignment,
    CRMTender,
    CRMTenderRepositoryDocument,
    CRMTechnicalService,
    CRMTicket,
)
from backend.schemas.crm.operations import (
    CustomerTicketCreate,
    CustomerTicketResponse,
    CustomerTicketUpdate,
    PMOProjectCreate,
    PMOProjectResponse,
    PMOProjectUpdate,
    SLAAssignmentCreate,
    SLAAssignmentResponse,
    SLAAssignmentUpdate,
    TechnicalServiceCreate,
    TechnicalServiceResponse,
    TechnicalServiceUpdate,
    TenderCreate,
    TenderDocumentCreate,
    TenderDocumentResponse,
    TenderDocumentUpdate,
    TenderResponse,
    TenderUpdate,
)


tenders_router = crud_router("/crm/tenders", "CRM Tenders", CRMTender, TenderCreate, TenderUpdate, TenderResponse, "Tender")
tender_documents_router = crud_router(
    "/crm/tender-documents",
    "CRM Tender Repository Documents",
    CRMTenderRepositoryDocument,
    TenderDocumentCreate,
    TenderDocumentUpdate,
    TenderDocumentResponse,
    "Tender document",
)
pmo_projects_router = crud_router(
    "/crm/pmo-projects",
    "CRM PMO Projects",
    CRMPMOProject,
    PMOProjectCreate,
    PMOProjectUpdate,
    PMOProjectResponse,
    "PMO project",
)
sla_assignments_router = crud_router(
    "/crm/sla-assignments",
    "CRM SLA Assignments",
    CRMSLAAssignment,
    SLAAssignmentCreate,
    SLAAssignmentUpdate,
    SLAAssignmentResponse,
    "SLA assignment",
)
technical_services_router = crud_router(
    "/crm/technical-services",
    "CRM Technical Services",
    CRMTechnicalService,
    TechnicalServiceCreate,
    TechnicalServiceUpdate,
    TechnicalServiceResponse,
    "Technical service",
)
customer_tickets_router = crud_router(
    "/crm/customer-tickets",
    "CRM Customer Tickets",
    CRMTicket,
    CustomerTicketCreate,
    CustomerTicketUpdate,
    CustomerTicketResponse,
    "Customer ticket",
)
