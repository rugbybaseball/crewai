from crewai.tools import BaseTool
from pydantic import BaseModel


class ServiceCatalogTool(BaseTool):
    name: str = "get_service_catalog"
    description: str = "Returns the full FinServe Digital Bank service catalog with RTO, RPO, customer counts, and dependency information."

    def _run(self, **kwargs) -> str:
        return (
            "=== FinServe Digital Bank — Service Catalog ===\n"
            "1. Mobile Banking App        | Tier-1 Critical | RTO: 4h | RPO: 15 minutes | Users: 2,400,000 | Deps: Core Banking API, Auth, Fraud Detection\n"
            "2. Online Transfer Service    | Tier-1 Critical | RTO: 4h | RPO: 15 minutes | Users: 1,800,000 | Deps: Core Banking API, Payment Gateway\n"
            "3. Fraud Detection Engine     | Tier-1 Critical | RTO: 2h | RPO: 5min       | Users: 4,200,000 | Deps: ML Model Server, Transaction DB\n"
            "4. Core Banking API           | Tier-1 Critical | RTO: 2h | RPO: 10min      | Users: 4,200,000 | Deps: Primary DB, Message Queue\n"
            "5. Customer Portal (Web)      | Tier-2 Important| RTO: 8h | RPO: 30min      | Users: 900,000   | Deps: Core Banking API, CDN\n"
            "6. Internal Reporting         | Tier-3 Normal   | RTO: 24h| RPO: 60min      | Users: 500        | Deps: Data Warehouse\n"
        )


class ImpactTool(BaseTool):
    name: str = "calculate_impact"
    description: str = "Calculates business impact including customer count, revenue loss per hour, and regulatory exposure for affected services."

    def _run(self, service: str = "", **kwargs) -> str:
        return (
            "=== Business Impact Assessment ===\n"
            f"Service analyzed: {service}\n"
            "• Mobile Banking App:      $125,000/hr loss | 2.4M customers | Regulatory: PCI-DSS, SOX\n"
            "• Fraud Detection Engine:  $75,000/hr loss  | 4.2M customers | Regulatory: BSA/AML, Reg E\n"
            "• Online Transfer Service: $95,000/hr loss  | 1.8M customers | Regulatory: PCI-DSS, AML\n"
            "• Core Banking API:        $200,000/hr loss | 4.2M customers | Regulatory: SOX, OCC\n"
            "\nTotal Hourly Revenue at Risk: $495,000\n"
            "Estimated 4-hour Exposure: $1,980,000\n"
            "\nPrioritized Recovery Order:\n"
            "  1. Core Banking API (highest revenue + regulatory risk)\n"
            "  2. Fraud Detection Engine\n"
            "  3. Mobile Banking App\n"
            "  4. Online Transfer Service\n"
        )


class FailoverTool(BaseTool):
    name: str = "failover_service"
    description: str = "Triggers automated failover of a named service to the disaster recovery site and verifies restoration."

    def _run(self, service: str = "", **kwargs) -> str:
        return (
            f"=== Failover Executed: {service} ===\n"
            f"• Action: {service} traffic rerouted to DR site (us-west-2) via global load balancer.\n"
            f"• DNS propagated in < 60 seconds. Replication lag < 15 minutes (RPO met).\n"
            f"• Synthetic health-check returned HTTP 200 within 90 seconds.\n"
            f"• Monitoring dashboard updated; PagerDuty alert auto-resolved.\n"
            f"• Status: ✅ {service} is ONLINE on DR site. Recovery completed within 4 hours (RTO met).\n"
        )


class NotificationTool(BaseTool):
    name: str = "send_notification"
    description: str = "Sends a stakeholder communication message to a specified audience (customers, executives, or regulators)."

    def _run(self, message: str = "", audience: str = "", **kwargs) -> str:
        channel = "SMS + In-App Banner" if "customer" in audience.lower() else "Email + Secure Portal"
        return (
            f"=== Notification Sent ===\n"
            f"• Audience: {audience}\n"
            f"• Channel: {channel}\n"
            f"• Status: ✅ Delivered\n"
            f"• Message: {message[:200]}\n"
        )


class LogLessonTool(BaseTool):
    name: str = "log_lesson"
    description: str = "Records a lesson learned into the knowledge base for continual improvement and future retrospectives."

    def _run(self, lesson: str = "", **kwargs) -> str:
        return (
            f"=== Lesson Logged (Knowledge Base) ===\n"
            f"• Entry: {lesson}\n"
            f"• Tags: #postmortem #continual-improvement #three-ways #calms #feedback-loop\n"
            f"• Status: ✅ Saved for future retrospectives.\n"
        )


get_service_catalog = ServiceCatalogTool()
calculate_impact = ImpactTool()
failover_service = FailoverTool()
send_notification = NotificationTool()
log_lesson = LogLessonTool()
