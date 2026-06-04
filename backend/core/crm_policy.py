CRM_DEPARTMENTS = [
    "HR",
    "Technical",
    "Sales",
    "Finance",
    "Operations",
    "Legal",
    "Bids",
    "PMO",
    "Presales",
    "Marketing",
]

CRM_DEPARTMENT_HEADS = {
    "Finance": "CFO",
    "Sales": "Sales Lead",
    "Technical": "CTO",
    "Bids": "CTO",
    "PMO": "CTO",
    "Presales": "CTO",
    "HR": "HR Lead",
    "Legal": "Legal Lead",
    "Operations": "Country Manager",
    "Marketing": "Marketing Lead",
}

CRM_PIPELINE_STAGES = [
    "Stage 1.a Discovery",
    "Stage 1.b Presentation/Demo/POC",
    "Stage 1.c RFP/Tender",
    "Stage 1.d Commit/Award",
    "Stage 2 Contracting & Legal Finalization",
    "Stage 3 Project Management Delivery & Implementation",
    "Stage 4 SLA Management & Support",
    "Stage 5 Renewal or Exit",
    "Stage 6.a Closed as Won",
    "Stage 6.b Closed as Lost",
]

OPEN_PIPELINE_STAGES = [
    "Stage 1.a Discovery",
    "Stage 1.b Presentation/Demo/POC",
    "Stage 1.c RFP/Tender",
    "Stage 1.d Commit/Award",
    "Stage 2 Contracting & Legal Finalization",
    "Stage 3 Project Management Delivery & Implementation",
    "Stage 4 SLA Management & Support",
    "Stage 5 Renewal or Exit",
]

CLOSED_WON_STAGE = "Stage 6.a Closed as Won"
CLOSED_LOST_STAGE = "Stage 6.b Closed as Lost"

PIPELINE_TYPES = [
    "Renewal/Exit",
    "New Business",
    "Upsell/Cross-sell",
]

SALES_ARENAS = [
    "Advisory",
    "Tailored Solutions",
    "Training Academy",
]

DEPARTMENT_RESPONSIBILITIES = {
    "Sales": "Own accounts, contacts, opportunities, pipeline, invoicing follow-up, debt collection, customer engagement, and GP target delivery.",
    "Bids": "Qualify RFP/tender requirements, coordinate bid/no-bid decisions, maintain submission timelines, and ensure compliant tender responses.",
    "Technical": "Own technical discovery, demos, POCs, solution design, vendor/distributor technical inputs, implementation handover, and support escalation.",
    "Presales": "Support AMs with solution architecture, BoQs, demos, POCs, and technical proposal content.",
    "PMO": "Own delivery planning, implementation milestones, project risks, acceptance, and handover into SLA/support.",
    "Legal": "Own contracting, legal review, risk clauses, compliance approvals, and contract finalization.",
    "Finance": "Own customer invoicing, vendor/distributor costs, margin validation, collections, and revenue recognition support.",
    "HR": "Own people allocation, hiring requests, performance alignment, and training readiness for delivery.",
    "Operations": "Coordinate country operations, regional delivery readiness, logistics, and country-level reporting.",
    "Marketing": "Own campaign support, event/workshop support, lead generation, and customer communication programs.",
}
