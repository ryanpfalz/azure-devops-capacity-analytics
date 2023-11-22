# azure-devops-capacity-analytics

---

| Page Type | Languages | Key Services | Tools    |
| --------- | --------- | ------------ | -------- |
| Sample    | Python    | Azure DevOps | Power BI |

---

# Performing Advanced Capacity Analytics with Azure DevOps

Azure DevOps provides the ability to set and analyze capacity for teams and team members [within sprint](https://learn.microsoft.com/en-us/azure/devops/boards/sprints/set-capacity?view=azure-devops) and at a [summarized level across teams](https://learn.microsoft.com/en-us/azure/devops/report/dashboards/widget-catalog?view=azure-devops#sprint-capacity-widget). However, there are times when you may want to perform more advanced analytics on capacity data, such as viewing capacity at a more granular level within a project, or across multiple projects. Using the Azure DevOps [Capacities APIs](https://learn.microsoft.com/en-us/rest/api/azure/devops/work/capacities/list?view=azure-devops-rest-6.0&viewFallbackFrom=azure-devops-rest-7.1&tabs=HTTP), you can retrieve capacity data and perform advanced analytics on it.
<br>
This codebase provides a demonstration of how to retrieve capacity data from the Azure DevOps Capacities API and visualize it in Power BI. A conceptual approach to automating the process for an enterprise setup is also provided.
<br>
The scenario presented in this codebase is simple not intended for production use, and should be viewed as a foundation for modification and expansion into more complex applications.

## Prerequisites

- [An Azure DevOps Organization and Project](https://learn.microsoft.com/en-us/azure/devops/user-guide/sign-up-invite-teammates?view=azure-devops&tabs=microsoft-account)
- [Power BI](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop)
- [Python](https://www.python.org/downloads/)
- [Optional - Azure Subscription](https://azure.microsoft.com/en-us/free/) - for building enterprise solution

## Running this sample

## Conceptual Enterprise Architecture & Workflow

![Diagram](./docs/images/automated-solution.png)

## Potential Business Use Cases

- There are multiple use cases for performing cross-project capacity analytics. For example:
  - In projects that involve multiple organizations (like joint ventures, partnerships, or consortia), cross-organizational capacity planning is crucial for coordinating efforts, timelines, and responsibilities.
  - It supports strategic decision-making by providing insights into the capabilities and limitations of different organizations, allowing for better long-term planning.
  - It helps in identifying bottlenecks and inefficiencies across organizations, leading to improved overall operational efficiency.
- Cross-team capacity analytics could be further complimented by [Azure DevOps Delivery Plans](https://learn.microsoft.com/en-us/azure/devops/boards/plans/add-edit-delivery-plan?view=azure-devops) and [Azure DevOps Analytics Views](https://learn.microsoft.com/en-us/azure/devops/report/powerbi/what-are-analytics-views?view=azure-devops).