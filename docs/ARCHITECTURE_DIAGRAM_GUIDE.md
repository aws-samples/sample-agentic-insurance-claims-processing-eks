# Architecture Diagram Guide

This guide explains how to use and customize the architecture diagram for the AI-Powered Insurance Claims Processing System.

---

## Overview

The architecture diagram provides a comprehensive visual representation of the entire system, including:

- AWS infrastructure components (VPC, ALB, EKS)
- Kubernetes constructs (Pods, Services, Ingress)
- Application components (Web Portal, Coordinator, Agents)
- Data stores (MongoDB, Redis)
- Monitoring and observability (CloudWatch)
- Data flows and connections

---

## File Location

The draw.io diagram file is located at:
```
architecture-diagram.drawio
```

---

## How to Open and Edit

### Option 1: Using draw.io Desktop App

1. **Download draw.io Desktop App**:
   - Visit: https://github.com/jgraph/drawio-desktop/releases
   - Download the appropriate version for your OS (Mac, Windows, Linux)
   - Install the application

2. **Open the Diagram**:
   - Launch draw.io Desktop
   - Click "Open Existing Diagram"
   - Navigate to `architecture-diagram.drawio`
   - Click "Open"

3. **Edit the Diagram**:
   - Click on any element to select it
   - Drag elements to reposition
   - Double-click text to edit
   - Use the left panel to add new shapes
   - Save changes with Cmd+S (Mac) or Ctrl+S (Windows)

### Option 2: Using draw.io Web (app.diagrams.net)

1. **Visit draw.io**:
   - Go to: https://app.diagrams.net/

2. **Open the File**:
   - Click "Open Existing Diagram"
   - Select "Device" (or your file storage location)
   - Navigate to and select `architecture-diagram.drawio`
   - Click "Open"

3. **Edit Online**:
   - Make your changes
   - Click "File" → "Save As" to save

4. **Export Options**:
   - File → Export as → PNG (for documentation)
   - File → Export as → SVG (for scalable graphics)
   - File → Export as → PDF (for presentations)

### Option 3: Using VS Code Extension

1. **Install Extension**:
   - Open VS Code
   - Go to Extensions (Cmd+Shift+X)
   - Search for "Draw.io Integration"
   - Install the extension by Henning Dieterichs

2. **Open Diagram**:
   - Right-click `architecture-diagram.drawio`
   - Select "Open With..." → "Draw.io Editor"
   - Edit directly in VS Code

---

## Diagram Components

### AWS Components (Orange/Yellow)

The diagram includes these AWS services with official icons:

- **Application Load Balancer (ALB)**: Entry point for user traffic
- **Amazon EKS**: Managed Kubernetes cluster
- **VPC**: Virtual Private Cloud for network isolation
- **CloudWatch**: Logging and monitoring service

**To add more AWS icons**:
1. Click the "+" icon in the left panel
2. Search for "AWS" in the shapes library
3. Browse AWS service icons
4. Drag and drop onto the canvas

### Kubernetes Components (Hexagons)

Kubernetes Pods are represented as hexagons with dark gray fill:

- Web Interface Pod (3 replicas)
- Coordinator Agent Pod (2 replicas)
- Claims Simulator Pod
- Redis Pod
- MongoDB Pod
- Ollama LLM Pod

**Color coding**:
- Blue: Web/Frontend components
- Green: Coordinator/Core logic
- Red/Pink: Data stores
- Purple: AI/ML components

### AI Agents (Colored Boxes)

Specialized agents in the lower section:

- **Policy Agent** (Blue): Policy validation
- **Fraud Agent** (Red): ML fraud detection
- **Risk Agent** (Orange): Risk scoring
- **External Agent** (Purple): Third-party integrations
- **LLM Agent** (Purple): Natural language processing

### Data Flow Arrows

Different arrow colors represent different types of connections:

- **Blue solid**: HTTPS/HTTP traffic
- **Green solid**: Internal Kubernetes services
- **Red solid**: REST API calls
- **Orange solid**: State management (Redis)
- **Green solid**: Data access (MongoDB)
- **Purple dashed**: LLM inference calls
- **Gray dashed**: Logging/monitoring

---

## Customizing the Diagram

### Changing Colors

1. **Select an element** by clicking on it
2. **Right-click** → "Edit Style"
3. **Change fill color**: Look for `fillColor=#HEXCODE`
4. **Change stroke**: Look for `strokeColor=#HEXCODE`
5. Click "Apply"

**Recommended color palette**:
- AWS Orange: `#FF9900`
- Kubernetes Blue: `#326CE5`
- Success Green: `#28A745`
- Warning Yellow: `#FFC107`
- Error Red: `#DC3545`
- Info Purple: `#6F42C1`

### Adding New Components

**To add a new Pod**:
1. Copy an existing pod container (Ctrl+C / Cmd+C)
2. Paste (Ctrl+V / Cmd+V)
3. Reposition the new pod
4. Double-click the text to edit
5. Update pod details (name, replicas, resources)

**To add a new AWS service**:
1. Click "+" in the left panel
2. Search for the AWS service (e.g., "S3", "DynamoDB")
3. Drag the icon onto the canvas
4. Add a label below the icon

**To add connections**:
1. Click the "Connector" tool (arrow icon in toolbar)
2. Click the source element
3. Click the target element
4. Double-click the line to add a label
5. Change line style in the format panel (right side)

### Updating Text

**To update component details**:
1. Double-click any text element
2. Type new content
3. Click outside to finish editing

**Text formatting**:
- Use `&xa;` for line breaks in XML (shows as new lines)
- Bold: Wrap with `<b></b>` or set `fontStyle=1`
- Italic: Wrap with `<i></i>` or set `fontStyle=2`
- Font size: Set `fontSize=12`

### Adjusting Layout

**To realign elements**:
1. Select multiple elements (Shift+Click)
2. Right-click → "Align" → Choose alignment option
3. Or use: "Arrange" → "Align" from top menu

**To distribute evenly**:
1. Select elements to distribute
2. "Arrange" → "Distribute" → Choose horizontal or vertical

**To group elements**:
1. Select multiple elements (Shift+Click or drag selection box)
2. Right-click → "Group"
3. Now they move together

---

## Exporting the Diagram

### For Documentation (PNG)

1. File → Export as → PNG
2. **Settings**:
   - Border Width: 10px
   - Zoom: 100%
   - Transparent Background: Unchecked
   - Selection Only: Unchecked
3. Choose resolution:
   - **Web**: 1x (standard)
   - **Print/Presentations**: 2x or 3x (high quality)
4. Click "Export"
5. Save as `architecture-diagram.png`

**Recommended settings**:
- Width: 1600-2000px for presentations
- Include: Border and shadow for professional look

### For Presentations (PDF)

1. File → Export as → PDF
2. **Settings**:
   - Fit to: 1 page
   - Page Format: Letter or A4
   - Orientation: Landscape
   - Border Width: 10px
3. Click "Export"
4. Save as `architecture-diagram.pdf`

### For Web (SVG)

1. File → Export as → SVG
2. **Settings**:
   - Transparent Background: Checked (for web embedding)
   - Include copy of diagram: Checked (allows editing)
3. Click "Export"
4. Save as `architecture-diagram.svg`

**Benefits of SVG**:
- Infinitely scalable
- Small file size
- Can be embedded in HTML
- Editable with text editors

### For Printing (High-Res PNG)

1. File → Export as → PNG
2. **Settings**:
   - Zoom: 300% or 400%
   - Border Width: 20px
   - DPI: 300 (if option available)
3. Click "Export"
4. Save as `architecture-diagram-print.png`

---

## Common Customizations

### Adding Your Company Logo

1. **Insert logo image**:
   - Click "+" → Search "Image"
   - Drag image shape to canvas
   - Double-click → "Choose Image"
   - Upload your logo file

2. **Position**:
   - Top-left corner: Company branding
   - Bottom-right: Watermark
   - Top-center: Title area

### Highlighting Specific Components

**To emphasize a component**:
1. Select the element
2. Edit Style → Add `shadow=1`
3. Increase `strokeWidth=3`
4. Use a brighter `fillColor`

**To add annotations**:
1. Insert a text box near the component
2. Add an arrow pointing to it
3. Use callout shapes for important notes

### Creating Multiple Versions

**For different audiences**:
1. Duplicate the diagram:
   - File → Save As → New filename
2. Simplify for executives:
   - Remove technical details
   - Keep only high-level components
   - Emphasize business value
3. Technical version:
   - Add IP addresses
   - Show port numbers
   - Include security groups

**Use layers** (if available):
1. View → Layers
2. Create layers: "Infrastructure", "Applications", "Data Flow"
3. Toggle visibility for different views

---

## Integration with Documentation

### Embedding in Markdown

**Using PNG**:
```markdown
![Architecture Diagram](./architecture-diagram.png)
```

**Using SVG**:
```markdown
![Architecture Diagram](./architecture-diagram.svg)
```

**With link to full diagram**:
```markdown
[![Architecture Diagram](./architecture-diagram-thumb.png)](./architecture-diagram.png)
*Click to view full-size diagram*
```

### In README Files

Add to your README.md:

```markdown
## Architecture

Below is the comprehensive system architecture showing all components:

![System Architecture](./architecture-diagram.png)

**Key Components:**
- AWS EKS cluster with auto-scaling
- Multi-agent AI system using LangGraph
- Four persona portals for different stakeholders
- MongoDB and Redis for data persistence
- CloudWatch for monitoring and observability

For the editable diagram, open `architecture-diagram.drawio` in [draw.io](https://app.diagrams.net/).
```

### In Presentations

1. **Export as high-res PNG** (3x zoom)
2. **Insert in PowerPoint/Keynote**:
   - Insert → Picture → From File
   - Select the exported PNG
3. **Animate sections** (optional):
   - Export individual layers/sections
   - Build slide-by-slide reveal

---

## Best Practices

### Design Guidelines

1. **Consistency**:
   - Use the same shape for similar components
   - Maintain consistent spacing between elements
   - Stick to the defined color palette

2. **Clarity**:
   - Avoid overlapping elements
   - Use clear, readable fonts (minimum 9pt)
   - Label all connections
   - Group related components

3. **Simplicity**:
   - Don't overcrowd the diagram
   - Use layers for complex systems
   - Create separate diagrams for different concerns
   - Hide details not relevant to the audience

4. **Professionalism**:
   - Align elements properly
   - Use consistent arrow styles
   - Include a legend
   - Add title and date

### Maintenance

1. **Version Control**:
   - Commit the .drawio file to Git
   - Tag versions: v1.0, v1.1, etc.
   - Include commit messages explaining changes

2. **Update Regularly**:
   - When architecture changes
   - After adding new services
   - When scaling patterns change
   - Document changes in commit messages

3. **Keep Exports Updated**:
   - Re-export PNG/PDF after changes
   - Update documentation images
   - Regenerate presentation materials

---

## Troubleshooting

### Issue: Diagram doesn't open

**Solution**:
- Ensure you have draw.io installed (desktop or web)
- Check file isn't corrupted: Open in text editor, should see XML
- Try opening in web version: https://app.diagrams.net/

### Issue: AWS icons missing

**Solution**:
- In draw.io, click "+" → Search "AWS"
- If AWS library not available: Click "More Shapes" → Enable "AWS 19"
- Use generic shapes as placeholders, then replace

### Issue: Exported image is blurry

**Solution**:
- Increase zoom level before export (try 200% or 300%)
- For print: Export at 3x or 4x zoom
- Use SVG format for perfect scaling

### Issue: Colors don't match brand guidelines

**Solution**:
- Define custom color palette in draw.io
- Use hex color codes from brand guidelines
- Apply consistently across all elements
- Document color codes in diagram legend

### Issue: Diagram too large to view

**Solution**:
- Use zoom controls (bottom-right)
- Fit to window: View → Fit
- For web display: Export at appropriate resolution
- Consider splitting into multiple diagrams

---

## Additional Resources

### Draw.io Documentation
- Official docs: https://www.diagrams.net/doc/
- Tutorials: https://www.diagrams.net/doc/getting-started-editor
- Keyboard shortcuts: https://www.diagrams.net/shortcuts

### AWS Architecture Icons
- Download official AWS icons: https://aws.amazon.com/architecture/icons/
- AWS Architecture Center: https://aws.amazon.com/architecture/

### Kubernetes Icons
- Kubernetes official icons: https://github.com/kubernetes/community/tree/master/icons
- CNCF Landscape: https://landscape.cncf.io/

### Diagram Best Practices
- C4 Model: https://c4model.com/
- AWS Well-Architected Framework: https://aws.amazon.com/architecture/well-architected/
- The Art of Visualising Software Architecture: https://leanpub.com/visualising-software-architecture

---

## Examples of Customizations

### For Sales/Marketing Materials

**Changes to make**:
- Remove technical details (IPs, ports, namespaces)
- Add business value callouts
- Use more vibrant colors
- Include customer logos (with permission)
- Add cost savings or efficiency gains
- Highlight unique features

**Example additions**:
- "$X cost savings per month"
- "94.7% AI accuracy"
- "2.3 min avg processing time"
- "99.9% uptime SLA"

### For Technical Documentation

**Changes to make**:
- Add specific configurations
- Include IP ranges and CIDR blocks
- Show port numbers
- Detail resource specifications (CPU, memory)
- Add security group rules
- Include IAM roles

**Example additions**:
- VPC CIDR: 10.0.0.0/16
- ALB Port: 80, 443
- MongoDB: 27017
- Redis: 6379
- EKS version: 1.33

### For Executive Presentations

**Changes to make**:
- Ultra-simplified view
- Focus on business outcomes
- Use minimal technical jargon
- Large, readable fonts
- Color-code by business function
- Add ROI indicators

**Example structure**:
- Layer 1: User Experience (portals)
- Layer 2: AI Intelligence (agents)
- Layer 3: Business Value (metrics)
- Bottom: Cloud Infrastructure (one box)

---

## Conclusion

The architecture diagram is a living document that should evolve with your system. Use this guide to:

1. **Open and edit** the diagram in draw.io
2. **Customize** for different audiences
3. **Export** in appropriate formats
4. **Integrate** into your documentation
5. **Maintain** as the system grows

The diagram is designed to be:
- **Comprehensive**: Shows all major components
- **Clear**: Easy to understand at a glance
- **Customizable**: Adapt to your specific needs
- **Professional**: Suitable for presentations and documentation

For questions or issues with the diagram, please refer to the draw.io documentation or create an issue in the GitHub repository.

Happy diagramming! 📊
