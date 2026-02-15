

# **从集合预测到实时感知：DEtection TRansformer家族的理论与技术综述**

## **引言**

### **物体检测的范式演进**

在DEtection TRansformer (DETR) 问世之前，物体检测领域长期由复杂的多阶段流程主导，这些流程严重依赖于人工设计的组件 1。以Faster R-CNN为代表的模型，其核心在于锚框（Anchor Boxes）、区域提议网络（Region Proposal Networks, RPNs）和非极大值抑制（Non-Maximum Suppression, NMS）等关键技术 2。这一范式虽然取得了巨大成功，但其固有的复杂性、对超参数的敏感性以及非端到端的特性，构成了该领域进一步发展的瓶颈 1。

### **DETR的核心主张：作为直接集合预测问题的物体检测**

2020年，DETR的出现标志着物体检测领域的一次根本性范式革命 6。受自然语言处理领域Transformer架构成功的启发，DETR首次将物体检测重新定义为一个直接的集合预测（Set Prediction）问题，从而构建了一个真正意义上的端到端（End-to-End）检测流程 4。该方法通过一个基于集合的全局损失函数，利用二分图匹配（Bipartite Matching）强制模型做出唯一的预测，从而彻底摒弃了对锚框、RPN和NMS等人工设计组件的依赖 2。

### **问题驱动的叙事结构**

本报告的核心论点是：DETR家族的演进是一系列针对其初始模型关键局限性的直接且系统性的回应。我们将详细阐述这些核心挑战——收敛速度慢、计算复杂度高以及对小物体检测性能不佳 1。本报告将以一种“问题驱动”的视角，清晰、逻辑地梳理该领域的技术脉络，将后续章节构建为对旨在解决这些问题的技术创新的深度探索 1。

### **报告路线图**

本报告将首先深入剖析DETR的基础范式，建立后续所有创新的基准。随后，我们将分阶段探讨为解决初始模型缺陷而涌现的关键技术，包括旨在降低复杂度和加速收敛的第一波创新，以及专注于稳定训练并达到业界顶尖性能的第二波技术浪潮。接着，报告将分析DETR如何演化为高效的实时检测模型，并简要概述其在分割、3D检测和多目标跟踪等领域的生态扩展。最后，我们将总结DETR的演进历程，并展望其未来的研究方向与挑战。

---

## **章节一：基础DETR范式：作为直接集合预测问题的物体检测**

本章节将对原始DETR模型进行深入的技术解构，为理解其后续演进奠定坚实的基础。

### **1.1 架构蓝图**

原始DETR的架构由三个核心部分组成：

1. **CNN骨干网络 (Backbone)**：通常采用预训练的卷积神经网络（如ResNet）来提取图像的底层特征图。随后，通过一个$1 \\times 1$的卷积层降低特征图的通道维度，为输入Transformer做准备 4。  
2. **Transformer编码器-解码器 (Encoder-Decoder)**：这是DETR的核心。  
   * **编码器**：接收来自CNN骨干网络的特征图，并利用多头自注意力（Multi-Head Self-Attention）机制对图像的全局上下文信息进行建模。由于Transformer本身不具备处理序列顺序的能力，因此在输入时需要加入固定的位置编码（Positional Encoding）来保留空间信息 5。  
   * **解码器**：接收编码器的输出以及一组固定的、可学习的“物体查询”（Object Queries）作为输入。通过自注意力和交叉注意力（Cross-Attention）机制，解码器能够并行地推理出每个物体的位置和类别 4。  
3. **预测头 (Prediction Heads)**：在解码器的输出端，每个物体查询都对应一个前馈网络（Feed-Forward Network, FFN）和一个线性层。FFN负责预测归一化的边界框坐标（中心点、宽度和高度），而线性层则通过Softmax函数输出类别标签。为了处理图像中物体数量不固定的情况，类别中包含一个特殊的“无物体”（no object）类别 5。

### **1.2 集合预测的实现**

DETR将物体检测视为一个集合预测问题，其实现依赖于以下几个关键机制：

* **作为可学习位置嵌入的物体查询**：DETR引入了一组固定数量（通常为$N=100$）的物体查询。这些查询是可学习的嵌入向量，在训练过程中，它们逐渐学会专注于图像中的特定区域和特定尺寸的物体，扮演着“插槽”的角色，等待被物体信息填充 4。  
* **二分图匹配与匈牙利算法**：这是DETR实现端到端的关键。模型输出的$N$个预测结果与图像中的真实物体标注（Ground Truth）之间，通过匈牙利算法（Hungarian Algorithm）寻找一个成本最低的一对一匹配 4。这种机制强制模型为每个真实物体生成一个唯一的预测，从而自然地消除了冗余检测，也使得NMS不再是必需的后处理步骤 2。  
* **基于集合的全局损失函数**：DETR的损失函数直接作用于匹配后的预测-真值对。它由两部分组成：用于分类的交叉熵损失，以及用于边界框定位的损失，后者是L1损失和泛化交并比（Generalized IoU, GIoU）损失的线性组合 2。由于匹配过程的存在，该损失函数天然地对预测结果的排列顺序不敏感。

### **1.3 告别传统：DETR 与 Faster R-CNN 的对比**

DETR的提出，代表了对传统检测流程的彻底颠覆。通过与Faster R-CNN的直接技术对比，我们可以更清晰地理解其范式上的简化与革新 4。

* **摒弃锚框与RPN**：Faster R-CNN依赖于在图像上预设的大量锚框和复杂的区域提议网络来生成候选区域。而DETR基于查询的机制完全绕过了这一过程，直接在全局特征上进行预测 1。  
* **消除NMS后处理**：二分图匹配的约束使得DETR的每个预测都具有唯一性，从而根除了传统方法中因大量重叠预测而必须依赖NMS进行筛选的问题。这使得DETR成为第一个真正意义上的全端到端检测器 1。  
* **全局上下文 vs. 局部区域**：Faster R-CNN的处理流程是基于局部区域的，它对每个提议区域进行独立的分类和回归。相比之下，DETR的Transformer编码器通过自注意力机制，能够同时处理整个图像的上下文信息，并建模所有物体之间的相互关系，这为其带来了独特的全局推理能力 2。

下表总结了DETR与Faster R-CNN在架构上的核心差异。

**表1：DETR与Faster R-CNN架构对比**

| 组件/阶段 | Faster R-CNN | DETR |
| :---- | :---- | :---- |
| **流程阶段** | 多阶段 (RPN \+ 检测头) | 单阶段 (端到端) |
| **区域提议** | 区域提议网络 (RPN) | 无 (直接预测) |
| **边界框先验** | 锚框 (Anchors) | 物体查询 (Object Queries) |
| **预测特征提取** | RoI池化/对齐 (局部特征) | 交叉注意力 (全局特征) |
| **冗余预测去除** | 非极大值抑制 (NMS) | 二分图匹配 (内置于损失) |
| **训练目标** | 分类损失 \+ 边界框回归损失 | 基于集合的全局损失 |
| **核心优势** | 对小物体检测性能较好 | 简化流程，对大物体性能优越 |
| **核心劣势** | 流程复杂，依赖人工设计组件 | 收敛慢，计算复杂度高 |

### **1.4 初露锋芒与严峻挑战**

尽管设计新颖，原始DETR在COCO等具有挑战性的数据集上，其准确率和推理速度与经过高度优化的Faster R-CNN基线相当 4。特别地，得益于Transformer的非局部计算能力和全局感受野，DETR在检测大物体方面表现出显著优势 4。

然而，这种范式上的突破也伴随着巨大的代价，其固有的缺陷为后续数年的研究指明了方向：

1. **收敛极其缓慢**：在COCO数据集上，DETR需要训练长达500个周期才能收敛，是传统检测器训练时长的10到20倍，这极大地增加了研究和开发的成本与周期 1。  
2. **高计算与内存复杂度**：Transformer编码器中自注意力机制的计算复杂度与输入特征图的像素数量成二次方关系 ($O(N^2)$)。这使得模型难以处理高分辨率的特征图，从而限制了其性能和应用场景 1。  
3. **小物体检测性能不佳**：高计算复杂度的直接后果是，DETR被迫只能使用来自骨干网络最后一层的低分辨率特征图。这导致了严重的细节信息丢失，使得模型在检测小物体时表现非常糟糕 1。

DETR的这些初始缺陷并非孤立存在，而是相互关联的。其缓慢的收敛和小物体检测的不足，本质上都源于同一个核心矛盾：在缺乏明确空间先验的情况下，全局、非局部的注意力机制与模糊的物体查询相结合，使得二分图匹配的学习任务异常困难。Transformer的交叉注意力模块必须从随机初始化的查询中，学会在广阔的特征图上定位到正确的空间位置并提取相关的语义特征 18。这是一个极具挑战的信用分配问题，导致训练初期的匹配极不稳定，从而拖慢了收敛速度 19。与此同时，编码器自注意力的二次方复杂度迫使模型使用粗糙的特征图，这在物理上抹去了检测小物体所必需的精细信息 1。因此，赋予DETR大物体检测优势的全局注意力机制，也正是其最大弱点的根源。后续的研究可以被看作是一个在不牺牲端到端范式的前提下，通过引入适度的归纳偏置（如空间先验、局部性）来约束这一困难学习问题的过程。

---

## **章节二：弥补核心缺陷：第一波创新浪潮**

面对原始DETR的严峻挑战，研究界迅速响应，催生了第一波旨在解决计算复杂度和查询模糊性问题的关键创新。

### **2.1 应对计算瓶颈与收敛难题**

#### **2.1.1 可变形注意力 (Deformable DETR)**

Deformable DETR是DETR家族中一个里程碑式的模型，它直接解决了注意力机制的二次方复杂度问题 14。

* **核心思想**：其核心创新在于引入了可变形注意力模块（Deformable Attention Module）。该模块不再让每个查询关注特征图上的所有像素点，而是只关注参考点周围一小组（数量固定）的关键采样点 21。  
* **工作机制**：这些采样点的偏移量是由查询本身通过一个小型网络学习得到的，这使得注意力能够自适应地聚焦于图像中的重要区域，其思想借鉴了可变形卷积 16。通过这种稀疏采样的方式，注意力的计算复杂度从与特征图像素数的二次方关系 ($O(N^2)$) 降低到了线性关系 ($O(N)$)。  
* **深远影响**：这一改变带来了两大革命性成果：  
  1. **显著加速收敛**：训练收敛所需的周期数减少了约10倍 14。  
  2. **启用多尺度特征**：由于注意力计算变得高效，模型得以处理来自骨干网络不同层级的高分辨率特征图。这直接弥补了原始DETR在小物体检测上的短板，极大地提升了模型在处理多尺度物体时的性能 13。

#### **2.1.2 其他收敛加速技术**

除了Deformable DETR，还有其他一些工作也从不同角度解决了收敛慢的问题。

* **Conditional DETR**：该模型通过在交叉注意力中解耦内容信息和空间信息来加速收敛 26。它从解码器上一层的输出中学习一个“条件式空间查询”（Conditional Spatial Query），引导注意力头关注物体的特定区域（如边界框的四个角点）。这降低了模型在训练早期对高质量内容嵌入的依赖，从而简化了学习过程 26。  
* **SAM-DETR (Semantic-Aligned Matching)**：此方法将交叉注意力过程重新诠释为“匹配与蒸馏” 18。它通过将物体查询投影到与图像特征相同的嵌入空间中，实现了语义上的对齐，从而使得匹配过程更加高效，进而加速了模型的收敛 18。

### **2.2 重新思考查询：从静态嵌入到动态锚框**

原始DETR的物体查询是抽象的可学习嵌入，缺乏明确的空间意义，这使得优化过程变得困难且不直观 28。

#### **2.2.1 DAB-DETR的创新**

DAB-DETR (Dynamic Anchor Boxes DETR) 通过一种全新的查询范式解决了这个问题。

* **核心思想**：DAB-DETR直接将查询定义为四维的边界框坐标 $(x, y, w, h)$ 29。这种做法为每个查询赋予了明确的空间先验信息。  
* **主要影响**：这种显式的坐标化查询极大地提升了查询与图像特征之间的相似度，进一步加速了收敛，并使得查询的角色变得清晰可解释 29。它在概念上架起了传统锚框方法与DETR查询机制之间的桥梁 34。

#### **2.2.2 逐层优化与注意力调制**

DAB-DETR的精髓不仅在于查询的定义，更在于其动态更新机制。

* **迭代式优化**：在解码器的每一层，锚框（即查询）都会被动态地更新和优化 29。这种逐层优化的过程形成了一种级联式的处理流程，可以被理解为一种软性的RoI池化（Soft RoI Pooling） 31。  
* **尺寸调制的注意力**：DAB-DETR巧妙地利用了锚框的宽度（$w$）和高度（$h$）信息来调制位置注意力图 29。这使得注意力机制能够根据不同尺度和长宽比的物体自适应地调整其关注范围，提供了比早期模型中固定的各向同性高斯先验更强大的空间引导 33。

这一波创新浪潮的核心主题是，通过引入受控的“局部性”或空间归纳偏置，来约束和引导DETR的学习过程。无论是Deformable DETR的稀疏采样、Conditional DETR的空间查询，还是DAB-DETR的动态锚框，都是在为原本纯粹全局的注意力机制提供有效的空间引导，使其学习任务变得更加明确和 tractable。Deformable DETR和DAB-DETR的突破并非相互竞争，而是相辅相成的。前者解决了编码器和解码器的**效率**问题，使得处理多尺度特征成为可能；后者则解决了查询的**模糊性**问题，为模型提供了明确的优化目标。它们的思想结合，为下一代更高性能的DETR模型奠定了坚实的架构基础。

---

## **章节三：第二波浪潮：稳定训练与登顶SOTA**

在解决了计算复杂度和查询表征的基础问题后，DETR的研究进入了一个更成熟的阶段。第二波创新浪潮将焦点从宏观的架构改造转向了微观的训练动力学优化，旨在解决训练过程中的不稳定性，从而将模型性能推向新的高度。

### **3.1 去噪训练范式**

#### **3.1.1 DN-DETR：探寻收敛缓慢的根源**

DN-DETR (DeNoising DETR) 的研究者们深刻地洞察到，DETR收敛缓慢的根本原因在于训练早期二分图匹配的不稳定性 19。在不同的训练周期中，同一个查询可能会被匹配到不同的物体上，这导致模型的优化目标前后不一，学习过程混乱而低效 19。

* **解决方案**：为了解决这一问题，DN-DETR引入了一种新颖的去噪（Denoising）训练任务。除了常规的匈牙利匹配损失外，模型还会接收一组加入了噪声的真实边界框（Ground-Truth Boxes），并通过一个额外的重建损失来学习恢复出原始的、干净的边界框 19。  
* **核心影响**：这个辅助的去噪任务之所以有效，是因为它绕过了不稳定的二分图匹配过程，为模型提供了一个直接且稳定的边界框回归学习信号。这可以被看作是一个“更简单”的任务，它帮助模型更快地学会如何进行精确的定位，从而极大地加速了整体的收敛速度并提升了最终性能 19。这一技术具有很强的通用性，可以方便地集成到任何DETR类的模型中 20。

#### **3.1.2 DINO：DETR集大成者**

DINO (DETR with Improved deNoising anchOr boxes) 是当前DETR家族中最先进的模型之一，它巧妙地融合并升华了其前辈们的诸多优点 38。

DINO的核心贡献在于三项关键技术：

1. **对比去噪训练 (Contrastive Denoising Training)**：这是对DN-DETR思想的进一步优化。DINO将同一个真实边界框的两个不同加噪版本同时送入模型，其中噪声较小的作为正样本，噪声较大的作为负样本。通过这种对比学习的方式，模型不仅学会了精确地预测边界框，还能有效地区分出细微的定位差异，从而显著减少了对同一目标的重复预测 38。  
2. **“向前看两次”机制 (Look Forward Twice Scheme)**：该技术旨在改进解码器中的逐层边界框优化过程。在传统的贪婪优化中，第$i-1$层的参数更新只考虑第$i-1$层的损失。而“向前看两次”机制允许来自第$i$层的梯度回传并影响第$i-1$层的参数更新。这克服了逐层优化的“短视”问题，使得模型能够进行更具前瞻性的、全局最优的边界框预测，从而在保持快速收敛的同时获得更高的精度 38。  
3. **混合查询选择 (Mixed Query Selection)**：这是一种更优的锚点初始化策略。DINO借鉴Deformable DETR，从编码器的输出中选择初始的**位置查询**，这为模型提供了强烈的空间先验。同时，它保留了可学习的**内容查询**。这种混合策略兼顾了空间先验的稳定性和内容学习的灵活性，实现了更优的初始化 38。

### **3.2 高级查询设计与优化**

随着模型架构和训练方法的成熟，研究者们开始更深入地探索查询本身的设计。

#### **3.2.1 内容自适应查询 (SACQ)**

* **问题**：传统的物体查询中，内容部分通常被初始化为零向量或可学习的嵌入，缺乏与输入图像相关的内容信息，这限制了其性能 34。  
* **解决方案**：自适应内容查询（Self-Adaptive Content Query, SACQ）模块利用Transformer编码器的输出特征，通过自注意力池化来生成与输入图像内容相关的查询。这使得查询能够自适应地携带更丰富的内容先验，从而更好地聚焦于目标物体 34。

#### **3.2.2 缓解查询竞争 (EASE-DETR)**

* **问题**：更优的查询设计可能导致多个查询同时高度关注同一个目标，从而引发激烈的“竞争”。在一对一的匈牙利匹配机制下，只有一个查询能成为“胜者”，其余相似的查询都会被抑制，这反而阻碍了训练 34。  
* **解决方案**：EASE-DETR提出了一种缓解竞争的策略。在解码器的中间层，它会识别出针对同一目标的“领先”查询（得分更高）和“落后”查询，并通过一个可学习的偏置来放大领先查询在下一层中的注意力得分。这有助于“胜者”更快地脱颖而出，从而稳定了训练过程并提升了准确性 42。

从第一波创新到第二波创新，DETR研究的重心发生了微妙而深刻的转变——从解决宏观的**架构缺陷**转向了优化微观的**训练动力学**。DINO的成功表明，当模型架构趋于成熟时，进一步提升性能的关键在于更深刻地理解和引导模型的学习过程。而去噪训练的引入，可以被视为一种隐式的课程学习（Curriculum Learning）。它首先为模型提供了一个不依赖于复杂匹配的、更简单的回归任务，让模型的核心部件（如特征表示和回归头）得到良好的预热和初始化。当模型掌握了这个“简单课程”后，再去解决更困难的、依赖于二分图匹配的联合优化任务，就会变得更加高效和稳定。

---

## **章节四：迈向实时性能与效率**

将DETR从一个理论上优雅但实践中缓慢的模型，转变为能够与YOLO系列等高效检测器相媲美的实时模型，是其发展历程中的又一重要篇章。这一转变是通过对架构、训练策略和监督方式的全方位优化实现的。

### **4.1 架构优化以提升速度**

#### **4.1.1 高效混合编码器 (RT-DETR)**

RT-DETR是首个真正意义上的实时端到端DETR模型，其核心在于其创新的高效混合编码器 43。

* **问题**：即便使用了可变形注意力，标准的Transformer编码器在处理多尺度特征时仍然是实时性能的瓶颈 44。  
* **解决方案**：RT-DETR的混合编码器巧妙地将特征处理过程解耦为两个部分：  
  1. **尺度内交互 (Intra-scale Interaction)**：使用计算高效的CNN模块（如ResNet块）在每个特征尺度内部进行交互。  
  2. 跨尺度融合 (Cross-scale Fusion)：使用轻量级的、基于注意力的模块来融合来自不同尺度的特征信息。  
     这种设计避免了在所有多尺度特征上进行全局自注意力计算所带来的巨大开销，显著提升了推理速度 43。

#### **4.1.2 稀疏与轻量化注意力机制**

为了进一步降低计算成本，研究者们探索了多种稀疏化和轻量化策略。

* **查询/令牌剪枝**：这类方法旨在通过智能地剔除冗余信息来减少注意力的计算量。例如，Sparse DETR通过一个可学习的模块来过滤掉大部分背景相关的图像令牌（tokens），只让少量包含前景信息的令牌进入编码器进行处理 1。Focus-DETR则更进一步，通过一个评分机制来识别信息量最丰富的令牌，并重构编码器使其专注于这些关键令牌 44。  
* **轻量化架构**：LW-DETR等模型则通过极致简化架构来追求速度。它采用了一个简单的ViT编码器，并搭配一个非常浅的（例如仅3层）DETR解码器，同时结合其他高效的训练技术，实现了卓越的实时性能 46。

### **4.2 训练与监督策略以提升效率**

#### **4.2.1 密集监督 (Co-DETR, RT-DETRv3)**

* **问题**：DETR标准的一对一匹配机制导致监督信号非常稀疏。在一张图像中，只有少数几个查询（与真实物体数量相等）能获得正向的梯度信号，而绝大多数查询都被指定为“无物体”。这种稀疏监督导致编码器和解码器的训练不够充分 48。  
* **解决方案**：研究者们借鉴了YOLO等密集检测器的思想，在训练阶段引入了辅助的密集监督。  
  * **Co-DETR**：在训练时引入了多个并行的辅助预测头。这些辅助头采用一对多（one-to-many）的标签分配策略（类似于Faster R-CNN或ATSS），为编码器提供了更丰富、更密集的监督信号，从而增强了其特征学习能力 49。  
  * **RT-DETRv3**：在RT-DETR的基础上，通过引入一个基于CNN的辅助分支和一个权重共享的解码器分支，提供了分层的密集正向监督，进一步提升了模型的性能和收敛速度 48。  
* **核心优势**：这些提供密集监督的辅助模块**仅在训练时使用**，在推理时会被完全丢弃。因此，它们能够在不增加任何推理延迟的情况下，显著提升模型的性能和训练效率 48。

DETR向实时性能的演进，很大程度上是在与YOLO系列模型的直接竞争中推动的。这种竞争压力促使研究者们超越了对纯粹准确率的追求，开始关注速度与精度的权衡，并催生了许多务实的架构创新。例如，RT-DETR的混合编码器实际上承认了纯Transformer并非处理所有视觉任务的最佳工具，通过重新引入高效的CNN进行尺度内特征提取，实现了“两全其美” 45。同样，采用一对多的密集监督策略，也是直接借鉴了YOLO等密集检测器的成功经验 48。这表明，实现实时性能并非依赖于单一的“银弹”技术，而是一个系统级的工程问题，需要对编码器、解码器、查询选择和训练策略进行协同优化。

---

## **章节五：不断扩展的DETR生态系统**

DETR范式的灵活性和通用性使其能够被成功地应用于物体检测之外的多种核心计算机视觉任务，极大地扩展了其影响力。

### **5.1 超越2D检测：全景分割**

* **核心适配**：将DETR扩展到全景分割（Panoptic Segmentation）在概念上非常直接。只需在Transformer解码器的输出之上增加一个掩码预测头（Mask Head）即可 2。对于每一个预测出边界框的物体查询，这个掩码头会同时预测一个像素级的二元掩码，从而实现实例分割。  
* **技术改进**：在基础DETR之上，Panoptic SegFormer等模型进行了进一步的优化。它通过采用深度监督的掩码解码器、为“事物”（things）和“材料”（stuff）类别设计解耦的查询策略，以及改进掩码合并的后处理方法，生成了更高保真度的分割结果 51。

### **5.2 迈入三维空间：3D物体检测**

* **挑战**：将DETR应用于3D领域的挑战在于如何有效处理稀疏的点云数据，或从多视角的2D图像中推理出3D几何结构。  
* **关键变体**：  
  * **3DETR**：直接在3D点云上进行操作。它使用Transformer来处理点云特征，而无需依赖于像PointNet++这样复杂的3D专用骨干网络 52。  
  * **DETR3D**：这是一个专为多摄像头3D物体检测设计的框架。它使用定义在3D空间中的物体查询，并通过相机内外参矩阵将这些3D查询投影到不同视角的2D图像特征上，从而建立了3D位置与2D视觉证据之间的联系 53。  
  * **MonoDETR**：该模型致力于解决极具挑战性的单目3D检测任务。它引入了一个深度引导的Transformer，通过预测一个辅助的深度图并利用一个深度编码器，为检测解码器提供关键的几何线索 55。

### **5.3 追踪时间轨迹：多目标跟踪**

* **核心适配**：DETR在多目标跟踪（Multi-Object Tracking, MOT）领域的应用，其核心思想是将瞬时的“物体查询”扩展为跨时间帧持续存在的“轨迹查询”（Track Queries） 56。每一个轨迹查询都代表了一个物体的完整运动轨迹。  
* **关键变体 (MOTR)**：MOTR模型展示了如何将DETR改造为一个端到端的跟踪器。其解码器同时处理两种查询：已存在的轨迹查询（用于更新被跟踪物体的位置）和新的检测查询（用于发现新出现的目标） 56。通过动态维护查询集合以及一个轨迹感知的标签分配策略来管理目标的出现和消失，MOTR构建了一个无需独立进行检测、特征提取和数据关联步骤的、完全端到端的跟踪系统 57。

DETR能够成功适配到分割、3D检测和跟踪等多种任务，揭示了其设计中最具通用性的核心概念——“物体查询”。这个查询机制不仅仅是预测2D边界框的工具，更是一个强大的、可学习的、用于“实例级推理”的抽象表征。在全景分割中，查询代表一个“事物”或“材料”实例；在3D检测中，它代表一个3D物体；在跟踪中，它代表一条完整的时空轨迹。这表明，通过改变查询所关注的信息（ attends to）以及它被训练去预测的目标，这个基于查询的框架可以灵活地应用于不同的模态和任务。这正是DETR范式强大生命力的关键所在。

---

## **结论与未来展望**

### **DETR的演进之路总结**

DETR的发展历程，是一部从一个充满理论魅力但实践中困难重重的学术构想，演变为一个包含众多高效、强大的业界顶尖模型的家族史。本报告以问题为导向，系统性地回顾了这一历程，展示了研究社区如何通过一系列精巧的创新，逐一攻克了收敛速度、计算复杂度和小物体检测性能等核心难题。从Deformable DETR的稀疏注意力，到DAB-DETR的动态锚框，再到DN-DETR和DINO的去噪训练，直至RT-DETR的实时架构，每一次重要的迭代都标志着对DETR内在机理更深层次的理解。

下表清晰地勾勒了这一问题驱动的演化路径。

**表2：核心DETR模型的问题驱动演化路径**

| 模型名称 | 解决的核心问题 | 核心技术创新 | 对性能/效率的影响 |
| :---- | :---- | :---- | :---- |
| **DETR** | 流程复杂，依赖人工组件 | 集合预测，二分图匹配 | 实现了端到端检测，但收敛慢、计算量大、小物体性能差 |
| **Deformable DETR** | 计算复杂度高，小物体性能差 | 可变形注意力，多尺度特征 | 线性复杂度，收敛速度提升10倍，显著改善小物体检测 |
| **DAB-DETR** | 查询含义模糊，收敛慢 | 4D动态锚框查询，逐层优化 | 明确了查询的空间意义，进一步加速收敛 |
| **DN-DETR** | 训练不稳定，收敛慢 | 去噪训练辅助任务 | 稳定了二分图匹配，显著加速收敛 |
| **DINO** | 训练不稳定，重复预测 | 对比去噪，"向前看两次"优化 | 达到SOTA性能，预测更精确，收敛更快 |
| **RT-DETR** | 推理速度慢，无法实时 | 高效混合编码器，解耦设计 | 首次实现DETR模型的实时端到端检测 |

### **当前的业界顶尖水平**

经过多年的发展，DETR家族的模型在标准的COCO基准测试上已经取得了与最优秀的CNN检测器相媲美甚至超越的性能。下表展示了部分关键模型在COCO验证集上的性能数据。

**表3：DETR变体在COCO验证集上的性能对比**

| 模型 | 骨干网络 | 训练周期 | AP | AP50 | AP75 | APs | APm | APl | 延迟(ms) |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Faster R-CNN | ResNet-50-FPN | 108 (9x) | 40.2 | 61.0 | 43.8 | 24.1 | 43.5 | 52.0 | \~62.5 |
| DETR | ResNet-50 | 500 | 42.0 | 62.4 | 44.2 | 20.5 | 45.8 | 61.1 | \~35.7 |
| Deformable DETR | ResNet-50 | 50 | 44.5 | 63.8 | 47.9 | 26.4 | 47.9 | 59.8 | \~23.8 |
| DINO | ResNet-50 | 24 | 51.3 | \- | \- | 33.7 | 54.5 | 65.5 | \- |
| RT-DETR-L | HGNetv2-L | \- | 54.8 | 72.8 | 59.3 | 37.5 | 58.6 | 70.0 | 10.9 |
| RF-DETR-M | \- | \- | 54.7 | 73.6 | \- | \- | \- | \- | 4.52 |

*注：性能数据来源于各模型原始论文或相关基准测试报告，测试条件（如硬件、批处理大小）可能存在差异，仅供参考。* 4

### **遗留挑战与未来方向**

尽管DETR取得了巨大成功，但仍有一些挑战和充满希望的研究方向值得探索：

* **极致的边缘端效率**：虽然RT-DETR等模型已经实现了实时性能，但要将DETR架构部署到计算资源极其有限的边缘设备（如微控制器）上，仍然是一个巨大的挑战。未来的研究将更多地关注模型量化、剪枝、知识蒸馏以及更轻量级的架构设计 17。  
* **鲁棒性与域适应**：提升DETR模型在恶劣天气条件（如雾、雨）下的鲁棒性，以及增强其在数据有限的情况下快速适应新领域的能力，是推动其在自动驾驶等关键领域应用的重要方向 61。  
* **密集与微小物体检测**：虽然对小物体的检测性能已大幅改善，但在航空影像等场景中，面对极端微小且密集分布的目标，固定数量查询的DETR模型仍然会遇到瓶颈。动态查询数量、更高效的特征表示等将是未来的研究重点 62。  
* **与视觉-语言模型的深度融合**：DETR基于查询的本质使其与语言指令具有天然的契合度。未来，DETR与大规模预训练的视觉-语言模型（VLMs）的深度融合，将极大地推动开放词汇检测（Open-Vocabulary Detection）、指代表达理解（Referring Expression Comprehension）等前沿领域的发展，使物体检测系统能够理解更复杂、更自然的语言指令 64。

综上所述，DETR不仅为物体检测领域带来了一次深刻的范式革命，其后续的演进历程也为解决复杂深度学习系统中的核心挑战提供了宝贵的经验和思路。作为一个仍在不断发展的技术体系，DETR及其背后的思想将继续在计算机视觉的未来中扮演至关重要的角色。

---

#### **Works cited**

1. A Review of DEtection TRansformer: From Basic Architecture to ..., accessed October 31, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12252279/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12252279/)  
2. Introduction to DETR (Detection Transformers): Everything You ..., accessed October 31, 2025, [https://www.lightly.ai/blog/detr](https://www.lightly.ai/blog/detr)  
3. \[20.05\] DETR \- DOCSAID, accessed October 31, 2025, [https://docsaid.org/en/papers/object-detection/detr/](https://docsaid.org/en/papers/object-detection/detr/)  
4. End-to-End Object Detection with Transformers, accessed October 31, 2025, [https://www.ecva.net/papers/eccv\_2020/papers\_ECCV/papers/123460205.pdf](https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123460205.pdf)  
5. Comparison of Faster-RCNN and Detection Transformer (DETR) | by ..., accessed October 31, 2025, [https://whatdhack.medium.com/comparison-of-faster-rcnn-and-detection-transformer-detr-f67c2f5a2a04](https://whatdhack.medium.com/comparison-of-faster-rcnn-and-detection-transformer-detr-f67c2f5a2a04)  
6. A Review of DEtection TRansformer: From Basic Architecture to Advanced Developments and Visual Perception Applications \- PubMed, accessed October 31, 2025, [https://pubmed.ncbi.nlm.nih.gov/40648209/](https://pubmed.ncbi.nlm.nih.gov/40648209/)  
7. End-to-End Object Detection with Transformers \- Meta Research \- Facebook, accessed October 31, 2025, [https://research.facebook.com/publications/end-to-end-object-detection-with-transformers/](https://research.facebook.com/publications/end-to-end-object-detection-with-transformers/)  
8. arXiv:2005.12872v3 \[cs.CV\] 28 May 2020, accessed October 31, 2025, [https://arxiv.org/pdf/2005.12872](https://arxiv.org/pdf/2005.12872)  
9. DEtection TRansformer (DETR) vs. YOLO for object detection. | by Fahim Rustamy, PhD, accessed October 31, 2025, [https://medium.com/@faheemrustamy/detection-transformer-detr-vs-yolo-for-object-detection-baeb3c50bc3](https://medium.com/@faheemrustamy/detection-transformer-detr-vs-yolo-for-object-detection-baeb3c50bc3)  
10. DETR: End-to-End Object Detection with Transformers | by Tanya Soni \- Medium, accessed October 31, 2025, [https://medium.com/@arithmancylabs/detr-end-to-end-object-detection-with-transformers-292f9d757145](https://medium.com/@arithmancylabs/detr-end-to-end-object-detection-with-transformers-292f9d757145)  
11. DETR \- Hugging Face, accessed October 31, 2025, [https://huggingface.co/docs/transformers/model\_doc/detr](https://huggingface.co/docs/transformers/model_doc/detr)  
12. DETR versus R-CNN Models: A Comparative Analysis of Performance in Vehicle Component and Damage Detection, accessed October 31, 2025, [https://fbmn.h-da.de/fileadmin/Dokumente/Studium/DS/WS23\_MDS\_Thesis\_Kai\_Hennig\_POS.pdf](https://fbmn.h-da.de/fileadmin/Dokumente/Studium/DS/WS23_MDS_Thesis_Kai_Hennig_POS.pdf)  
13. Deformable attention — tackling DETRs runtime complexity | by Tilo Flasche | Medium, accessed October 31, 2025, [https://medium.com/@tnodecode/multi-scale-deformable-attention-tackling-detrs-runtime-complexity-and-problems-with-small-9c35bd969f48](https://medium.com/@tnodecode/multi-scale-deformable-attention-tackling-detrs-runtime-complexity-and-problems-with-small-9c35bd969f48)  
14. Deformable DETR: Deformable Transformers for End-to-End Object Detection \- SciSpace, accessed October 31, 2025, [https://scispace.com/pdf/deformable-detr-deformable-transformers-for-end-to-end-105syp985u.pdf](https://scispace.com/pdf/deformable-detr-deformable-transformers-for-end-to-end-105syp985u.pdf)  
15. Do-DETR: enhancing DETR training convergence with integrated denoising and RoI mechanism | Request PDF \- ResearchGate, accessed October 31, 2025, [https://www.researchgate.net/publication/390141609\_Do-DETR\_enhancing\_DETR\_training\_convergence\_with\_integrated\_denoising\_and\_RoI\_mechanism](https://www.researchgate.net/publication/390141609_Do-DETR_enhancing_DETR_training_convergence_with_integrated_denoising_and_RoI_mechanism)  
16. Paper Review: Deformable Transformers for End-to-End Object Detection., accessed October 31, 2025, [https://cenk-bircanoglu.medium.com/paper-review-deformable-transformers-for-end-to-end-object-detection-ed0a452f775f](https://cenk-bircanoglu.medium.com/paper-review-deformable-transformers-for-end-to-end-object-detection-ed0a452f775f)  
17. SpeedDETR: Speed-aware Transformers for End-to-end Object Detection \- Proceedings of Machine Learning Research, accessed October 31, 2025, [https://proceedings.mlr.press/v202/dong23b/dong23b.pdf](https://proceedings.mlr.press/v202/dong23b/dong23b.pdf)  
18. Accelerating DETR Convergence via Semantic-Aligned Matching \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/CVPR2022/papers/Zhang\_Accelerating\_DETR\_Convergence\_via\_Semantic-Aligned\_Matching\_CVPR\_2022\_paper.pdf](https://openaccess.thecvf.com/content/CVPR2022/papers/Zhang_Accelerating_DETR_Convergence_via_Semantic-Aligned_Matching_CVPR_2022_paper.pdf)  
19. DN-DETR: Accelerate DETR Training by Introducing Query ... \- arXiv, accessed October 31, 2025, [https://arxiv.org/pdf/2203.01305](https://arxiv.org/pdf/2203.01305)  
20. DN-DETR: Accelerate DETR Training by Introducing Query DeNoising, accessed October 31, 2025, [https://www.computer.org/csdl/journal/tp/2024/04/10334480/1St7xbgtENa](https://www.computer.org/csdl/journal/tp/2024/04/10334480/1St7xbgtENa)  
21. Deformable DETR: Deformable Transformers for End-to-End Object Detection. \- GitHub, accessed October 31, 2025, [https://github.com/fundamentalvision/Deformable-DETR](https://github.com/fundamentalvision/Deformable-DETR)  
22. Deformable DETR: Deformable Transformers for End-to-End Object ..., accessed October 31, 2025, [https://arxiv.org/abs/2010.04159](https://arxiv.org/abs/2010.04159)  
23. Deformable DETR: Deformable Transformers for End-to-End Object Detection | OpenReview, accessed October 31, 2025, [https://openreview.net/forum?id=gZ9hCDWe6ke](https://openreview.net/forum?id=gZ9hCDWe6ke)  
24. Deformable DETR \- Hugging Face, accessed October 31, 2025, [https://huggingface.co/docs/transformers/v4.41.2/model\_doc/deformable\_detr](https://huggingface.co/docs/transformers/v4.41.2/model_doc/deformable_detr)  
25. Deformable DETR \- YouTube, accessed October 31, 2025, [https://www.youtube.com/watch?v=9UG4amweIjk](https://www.youtube.com/watch?v=9UG4amweIjk)  
26. Conditional DETR for Fast Training Convergence \- arXiv, accessed October 31, 2025, [https://arxiv.org/html/2108.06152](https://arxiv.org/html/2108.06152)  
27. \[PDF\] Accelerating DETR Convergence via Semantic-Aligned Matching, accessed October 31, 2025, [https://www.semanticscholar.org/paper/2402865faf1af2f2c1286ebdd2585e1ca806a935](https://www.semanticscholar.org/paper/2402865faf1af2f2c1286ebdd2585e1ca806a935)  
28. Object Detection with Transformers: A Review \- PMC, accessed October 31, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12526829/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12526829/)  
29. DAB-DETR: Dynamic Anchor Boxes are Better Queries for DETR | Request PDF \- ResearchGate, accessed October 31, 2025, [https://www.researchgate.net/publication/358232679\_DAB-DETR\_Dynamic\_Anchor\_Boxes\_are\_Better\_Queries\_for\_DETR](https://www.researchgate.net/publication/358232679_DAB-DETR_Dynamic_Anchor_Boxes_are_Better_Queries_for_DETR)  
30. \[ICLR 2022\] Official implementation of the paper "DAB-DETR: Dynamic Anchor Boxes are Better Queries for DETR" \- GitHub, accessed October 31, 2025, [https://github.com/IDEA-Research/DAB-DETR](https://github.com/IDEA-Research/DAB-DETR)  
31. DAB-DETR \- Hugging Face, accessed October 31, 2025, [https://huggingface.co/docs/transformers/model\_doc/dab-detr](https://huggingface.co/docs/transformers/model_doc/dab-detr)  
32. DAB-DETR \- Hugging Face, accessed October 31, 2025, [https://huggingface.co/docs/transformers/main/model\_doc/dab-detr](https://huggingface.co/docs/transformers/main/model_doc/dab-detr)  
33. DAB-DETR: Dynamic Anchor Boxes are Better Queries for DETR, accessed October 31, 2025, [https://arxiv.org/pdf/2201.12329](https://arxiv.org/pdf/2201.12329)  
34. Enhancing DETR's Variants through Improved Content Query and Similar Query Aggregation \- arXiv, accessed October 31, 2025, [https://arxiv.org/html/2405.03318v1](https://arxiv.org/html/2405.03318v1)  
35. \[2203.01305\] DN-DETR: Accelerate DETR Training by Introducing Query DeNoising \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2203.01305](https://arxiv.org/abs/2203.01305)  
36. Adding Training Noise To Improve Detections — The Denoising Mechanism | by Uri Almog | Data Science Collective | Medium, accessed October 31, 2025, [https://medium.com/data-science-collective/adding-training-noise-to-improve-detections-the-denoising-mechanism-2060b52f0d23](https://medium.com/data-science-collective/adding-training-noise-to-improve-detections-the-denoising-mechanism-2060b52f0d23)  
37. DN-DETR: Accelerate DETR Training by Introducing Query DeNoising \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/CVPR2022/papers/Li\_DN-DETR\_Accelerate\_DETR\_Training\_by\_Introducing\_Query\_DeNoising\_CVPR\_2022\_paper.pdf](https://openaccess.thecvf.com/content/CVPR2022/papers/Li_DN-DETR_Accelerate_DETR_Training_by_Introducing_Query_DeNoising_CVPR_2022_paper.pdf)  
38. DINO: DETR WITH IMPROVED DENOISING ANCHOR \- OpenReview, accessed October 31, 2025, [https://openreview.net/pdf?id=3mRwyG5one](https://openreview.net/pdf?id=3mRwyG5one)  
39. DINO: DETR with Improved DeNoising Anchor Boxes for End-to-End Object Detection, accessed October 31, 2025, [https://www.researchgate.net/publication/359079872\_DINO\_DETR\_with\_Improved\_DeNoising\_Anchor\_Boxes\_for\_End-to-End\_Object\_Detection](https://www.researchgate.net/publication/359079872_DINO_DETR_with_Improved_DeNoising_Anchor_Boxes_for_End-to-End_Object_Detection)  
40. \[2203.03605\] DINO: DETR with Improved DeNoising Anchor Boxes for End-to-End Object Detection \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2203.03605](https://arxiv.org/abs/2203.03605)  
41. arxiv.org, accessed October 31, 2025, [https://arxiv.org/abs/2405.03318](https://arxiv.org/abs/2405.03318)  
42. EASE-DETR: Easing the Competition among Object Queries \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/CVPR2024/papers/Gao\_EASE-DETR\_Easing\_the\_Competition\_among\_Object\_Queries\_CVPR\_2024\_paper.pdf](https://openaccess.thecvf.com/content/CVPR2024/papers/Gao_EASE-DETR_Easing_the_Competition_among_Object_Queries_CVPR_2024_paper.pdf)  
43. RT-DETRv3: Real-time End-to-End Object Detection with Hierarchical Dense Positive Supervision \- arXiv, accessed October 31, 2025, [https://arxiv.org/html/2409.08475v1](https://arxiv.org/html/2409.08475v1)  
44. Less is More: Focus Attention for Efficient DETR \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/ICCV2023/papers/Zheng\_Less\_is\_More\_Focus\_Attention\_for\_Efficient\_DETR\_ICCV\_2023\_paper.pdf](https://openaccess.thecvf.com/content/ICCV2023/papers/Zheng_Less_is_More_Focus_Attention_for_Efficient_DETR_ICCV_2023_paper.pdf)  
45. RT-DETR: The Next Evolution in Real-Time Object Detection | by Nandini Lokesh Reddy, accessed October 31, 2025, [https://medium.com/@nandinilreddy/rt-detr-the-next-evolution-in-real-time-object-detection-aa1c7880f368](https://medium.com/@nandinilreddy/rt-detr-the-next-evolution-in-real-time-object-detection-aa1c7880f368)  
46. arXiv:2406.03459v1 \[cs.CV\] 5 Jun 2024, accessed October 31, 2025, [https://arxiv.org/pdf/2406.03459](https://arxiv.org/pdf/2406.03459)  
47. LW-DETR: A Transformer Replacement to YOLO for Real-Time Detection \- arXiv, accessed October 31, 2025, [https://arxiv.org/html/2406.03459v1](https://arxiv.org/html/2406.03459v1)  
48. \[2409.08475\] RT-DETRv3: Real-time End-to-End Object Detection with Hierarchical Dense Positive Supervision \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2409.08475](https://arxiv.org/abs/2409.08475)  
49. \[2211.12860\] DETRs with Collaborative Hybrid Assignments Training \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2211.12860](https://arxiv.org/abs/2211.12860)  
50. \[2502.17843\] Automatic Vehicle Detection using DETR: A Transformer-Based Approach for Navigating Treacherous Roads \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2502.17843](https://arxiv.org/abs/2502.17843)  
51. Panoptic SegFormer: Delving Deeper into Panoptic ... \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2109.03814](https://arxiv.org/abs/2109.03814)  
52. Code & Models for 3DETR \- an End-to-end transformer model for 3D object detection \- GitHub, accessed October 31, 2025, [https://github.com/facebookresearch/3detr](https://github.com/facebookresearch/3detr)  
53. WangYueFt/detr3d \- GitHub, accessed October 31, 2025, [https://github.com/WangYueFt/detr3d](https://github.com/WangYueFt/detr3d)  
54. DETR3D, accessed October 31, 2025, [https://tsinghua-mars-lab.github.io/detr3d/](https://tsinghua-mars-lab.github.io/detr3d/)  
55. MonoDETR: Depth-guided Transformer for Monocular 3D Object Detection \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/ICCV2023/papers/Zhang\_MonoDETR\_Depth-guided\_Transformer\_for\_Monocular\_3D\_Object\_Detection\_ICCV\_2023\_paper.pdf](https://openaccess.thecvf.com/content/ICCV2023/papers/Zhang_MonoDETR_Depth-guided_Transformer_for_Monocular_3D_Object_Detection_ICCV_2023_paper.pdf)  
56. MOTR: End-to-End Multi-Object Tracking with Transformers – CV ..., accessed October 31, 2025, [https://cv-tricks.com/how-to/motr-end-to-end-multi-object-tracking-with-transformers/](https://cv-tricks.com/how-to/motr-end-to-end-multi-object-tracking-with-transformers/)  
57. MOTR: End-to-End Multiple-Object Tracking with Transformer, accessed October 31, 2025, [https://www.ecva.net/papers/eccv\_2022/papers\_ECCV/papers/136870648.pdf](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136870648.pdf)  
58. Advancing State of the Art Object Detection (Again) with RF-DETR, accessed October 31, 2025, [https://blog.roboflow.com/rf-detr-nano-small-medium/](https://blog.roboflow.com/rf-detr-nano-small-medium/)  
59. Benchmarks \- RF-DETR \- Roboflow, accessed October 31, 2025, [https://rfdetr.roboflow.com/1.3.0/learn/benchmarks/](https://rfdetr.roboflow.com/1.3.0/learn/benchmarks/)  
60. NAN-DETR: noising multi-anchor makes DETR better for object detection \- Frontiers, accessed October 31, 2025, [https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2024.1484088/full](https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2024.1484088/full)  
61. Report: Weather-Aware Object Detection Transformer for Domain Adaptation \- arXiv, accessed October 31, 2025, [https://arxiv.org/html/2504.10877v1](https://arxiv.org/html/2504.10877v1)  
62. Dome-DETR: DETR with Density-Oriented Feature-Query Manipulation for Efficient Tiny Object Detection \- arXiv, accessed October 31, 2025, [https://arxiv.org/html/2505.05741v2](https://arxiv.org/html/2505.05741v2)  
63. Dome-DETR: DETR with Density-Oriented Feature-Query Manipulation for Efficient Tiny Object Detection \- arXiv, accessed October 31, 2025, [https://arxiv.org/html/2505.05741v1](https://arxiv.org/html/2505.05741v1)  
64. Real-time Transformer-based Open-Vocabulary Detection with Efficient Fusion Head \- arXiv, accessed October 31, 2025, [https://arxiv.org/html/2403.06892v2](https://arxiv.org/html/2403.06892v2)  
65. RF-DETR: A SOTA Real-Time Object Detection Model \- Roboflow Blog, accessed October 31, 2025, [https://blog.roboflow.com/rf-detr/](https://blog.roboflow.com/rf-detr/)  
66. End-to-End Object Detection with Transformers | springerprofessional.de, accessed October 31, 2025, [https://www.springerprofessional.de/en/end-to-end-object-detection-with-transformers/18547378](https://www.springerprofessional.de/en/end-to-end-object-detection-with-transformers/18547378)  
67. End-to-End Object Detection with Transformers | Request PDF \- ResearchGate, accessed October 31, 2025, [https://www.researchgate.net/publication/346022004\_End-to-End\_Object\_Detection\_with\_Transformers](https://www.researchgate.net/publication/346022004_End-to-End_Object_Detection_with_Transformers)  
68. End-to-End Object Detection with Transformers \- Deep Learning Reviews, accessed October 31, 2025, [https://www.dl.reviews/2020/06/06/object-detection-with-transformers/](https://www.dl.reviews/2020/06/06/object-detection-with-transformers/)  
69. DN-DETR: Accelerate DETR Training by Introducing Query DeNoising \- ResearchGate, accessed October 31, 2025, [https://www.researchgate.net/publication/363906792\_DN-DETR\_Accelerate\_DETR\_Training\_by\_Introducing\_Query\_DeNoising](https://www.researchgate.net/publication/363906792_DN-DETR_Accelerate_DETR_Training_by_Introducing_Query_DeNoising)  
70. DN-DETR: Accelerate DETR Training by Introducing Query DeNoising \- PubMed, accessed October 31, 2025, [https://pubmed.ncbi.nlm.nih.gov/38019624/](https://pubmed.ncbi.nlm.nih.gov/38019624/)  
71. Delving Deeper into Panoptic Segmentation with Transformers \- arXiv, accessed October 31, 2025, [https://arxiv.org/pdf/2109.03814](https://arxiv.org/pdf/2109.03814)  
72. This is the official repo of Panoptic SegFormer \[CVPR'22\] \- GitHub, accessed October 31, 2025, [https://github.com/zhiqi-li/Panoptic-SegFormer](https://github.com/zhiqi-li/Panoptic-SegFormer)  
73. Delving Deeper Into Panoptic Segmentation With Transformers \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/CVPR2022/papers/Li\_Panoptic\_SegFormer\_Delving\_Deeper\_Into\_Panoptic\_Segmentation\_With\_Transformers\_CVPR\_2022\_paper.pdf](https://openaccess.thecvf.com/content/CVPR2022/papers/Li_Panoptic_SegFormer_Delving_Deeper_Into_Panoptic_Segmentation_With_Transformers_CVPR_2022_paper.pdf)  
74. Panoptic SegFormer: Delving Deeper into Panoptic Segmentation with Transformers | Request PDF \- ResearchGate, accessed October 31, 2025, [https://www.researchgate.net/publication/362153252\_Panoptic\_SegFormer\_Delving\_Deeper\_into\_Panoptic\_Segmentation\_with\_Transformers](https://www.researchgate.net/publication/362153252_Panoptic_SegFormer_Delving_Deeper_into_Panoptic_Segmentation_with_Transformers)  
75. \[PDF\] DAB-DETR: Dynamic Anchor Boxes are Better Queries for DETR | Semantic Scholar, accessed October 31, 2025, [https://www.semanticscholar.org/paper/DAB-DETR%3A-Dynamic-Anchor-Boxes-are-Better-Queries-Liu-Li/004f1d2b1b7d7dcecafdd94daee9c1b0aa3e65cf](https://www.semanticscholar.org/paper/DAB-DETR%3A-Dynamic-Anchor-Boxes-are-Better-Queries-Liu-Li/004f1d2b1b7d7dcecafdd94daee9c1b0aa3e65cf)  
76. \[2201.12329\] DAB-DETR: Dynamic Anchor Boxes are Better Queries for DETR \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2201.12329](https://arxiv.org/abs/2201.12329)  
77. Conditional DETR for Fast Training Convergence \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/ICCV2021/papers/Meng\_Conditional\_DETR\_for\_Fast\_Training\_Convergence\_ICCV\_2021\_paper.pdf](https://openaccess.thecvf.com/content/ICCV2021/papers/Meng_Conditional_DETR_for_Fast_Training_Convergence_ICCV_2021_paper.pdf)  
78. Open-Vocabulary DETR with Conditional Matching, accessed October 31, 2025, [https://www.ecva.net/papers/eccv\_2022/papers\_ECCV/papers/136690107.pdf](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136690107.pdf)  
79. \[PDF\] Conditional DETR for Fast Training Convergence \- Semantic Scholar, accessed October 31, 2025, [https://www.semanticscholar.org/paper/Conditional-DETR-for-Fast-Training-Convergence-Meng-Chen/1cd6b0f41d62aca38ba5a69db10e79c05e618c21](https://www.semanticscholar.org/paper/Conditional-DETR-for-Fast-Training-Convergence-Meng-Chen/1cd6b0f41d62aca38ba5a69db10e79c05e618c21)  
80. An End-to-End Transformer Model for 3D Object Detection, accessed October 31, 2025, [https://facebookresearch.github.io/3detr/](https://facebookresearch.github.io/3detr/)  
81. An End-to-End Transformer Model for 3D Object Detection | Request PDF \- ResearchGate, accessed October 31, 2025, [https://www.researchgate.net/publication/354652676\_An\_End-to-End\_Transformer\_Model\_for\_3D\_Object\_Detection](https://www.researchgate.net/publication/354652676_An_End-to-End_Transformer_Model_for_3D_Object_Detection)  
82. RF-DETR is a real-time object detection and segmentation model architecture developed by Roboflow, SOTA on COCO and designed for fine-tuning. \- GitHub, accessed October 31, 2025, [https://github.com/roboflow/rf-detr](https://github.com/roboflow/rf-detr)  
83. RF-DETR Object Detection vs YOLOv12 : A Study of Transformer-based and CNN-based Architectures for Single-Class and Multi-Class Greenfruit Detection in Complex Orchard Environments Under Label Ambiguity \- arXiv, accessed October 31, 2025, [https://arxiv.org/html/2504.13099v1](https://arxiv.org/html/2504.13099v1)  
84. Sparse DETR \- ICLR, accessed October 31, 2025, [https://iclr.cc/media/iclr-2022/Slides/7017.pdf](https://iclr.cc/media/iclr-2022/Slides/7017.pdf)  
85. Sparse Semi-DETR: Sparse Learnable Queries for Semi-Supervised Object Detection \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/CVPR2024/papers/Shehzadi\_Sparse\_Semi-DETR\_Sparse\_Learnable\_Queries\_for\_Semi-Supervised\_Object\_Detection\_CVPR\_2024\_paper.pdf](https://openaccess.thecvf.com/content/CVPR2024/papers/Shehzadi_Sparse_Semi-DETR_Sparse_Learnable_Queries_for_Semi-Supervised_Object_Detection_CVPR_2024_paper.pdf)  
86. DETR3D: 3D Object Detection from Multi-view Images via 3D-to-2D Queries, accessed October 31, 2025, [https://patrick-llgc.github.io/Learning-Deep-Learning/paper\_notes/detr3d.html](https://patrick-llgc.github.io/Learning-Deep-Learning/paper_notes/detr3d.html)  
87. DQ3D: Depth-guided Query for Transformer-Based 3D Object Detection in Traffic Scenarios, accessed October 31, 2025, [https://arxiv.org/html/2510.23144v1](https://arxiv.org/html/2510.23144v1)  
88. \[PDF\] DETR3D: 3D Object Detection from Multi-view Images via 3D-to-2D Queries, accessed October 31, 2025, [https://www.semanticscholar.org/paper/DETR3D%3A-3D-Object-Detection-from-Multi-view-Images-Wang-Guizilini/48e2d76d35b44edc21d09d460021103ce997c804](https://www.semanticscholar.org/paper/DETR3D%3A-3D-Object-Detection-from-Multi-view-Images-Wang-Guizilini/48e2d76d35b44edc21d09d460021103ce997c804)  
89. Mix and Match: ByteTrack with DETR | CS231n \- Stanford University, accessed October 31, 2025, [https://cs231n.stanford.edu/2024/papers/mix-and-match-bytetrack-with-detr.pdf](https://cs231n.stanford.edu/2024/papers/mix-and-match-bytetrack-with-detr.pdf)  
90. ZhangGongjie/SAM-DETR \- Official PyTorch Implementation \- GitHub, accessed October 31, 2025, [https://github.com/ZhangGongjie/SAM-DETR](https://github.com/ZhangGongjie/SAM-DETR)  
91. Align-DETR: Enhancing End-to-end Object Detection with Aligned Loss \- BMVA Archive, accessed October 31, 2025, [https://bmva-archive.org.uk/bmvc/2024/papers/Paper\_211/paper.pdf](https://bmva-archive.org.uk/bmvc/2024/papers/Paper_211/paper.pdf)  
92. \[2203.06883\] Accelerating DETR Convergence via Semantic-Aligned Matching \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2203.06883](https://arxiv.org/abs/2203.06883)  
93. \[2502.00315\] MonoDINO-DETR: Depth-Enhanced Monocular 3D Object Detection Using a Vision Foundation Model \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2502.00315](https://arxiv.org/abs/2502.00315)  
94. IDEA-Research/DINO: \[ICLR 2023\] Official implementation of the paper "DINO: DETR with Improved DeNoising Anchor Boxes for End-to-End Object Detection" \- GitHub, accessed October 31, 2025, [https://github.com/IDEA-Research/DINO](https://github.com/IDEA-Research/DINO)  
95. Dino | PDF | Applied Mathematics | Computing \- Scribd, accessed October 31, 2025, [https://www.scribd.com/document/932263242/Dino](https://www.scribd.com/document/932263242/Dino)  
96. DINO: DETR with Improved DeNoising Anchor Boxes for End-to-End Object Detection, accessed October 31, 2025, [https://openreview.net/forum?id=3mRwyG5one](https://openreview.net/forum?id=3mRwyG5one)  
97. DETRs Beat YOLOs on Real-time Object Detection \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao\_DETRs\_Beat\_YOLOs\_on\_Real-time\_Object\_Detection\_CVPR\_2024\_paper.pdf](https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao_DETRs_Beat_YOLOs_on_Real-time_Object_Detection_CVPR_2024_paper.pdf)  
98. RT-DETR: Paper Explanation and Inference \- DebuggerCafe, accessed October 31, 2025, [https://debuggercafe.com/rt-detr/](https://debuggercafe.com/rt-detr/)  
99. \[2304.08069\] DETRs Beat YOLOs on Real-time Object Detection \- arXiv, accessed October 31, 2025, [https://arxiv.org/abs/2304.08069](https://arxiv.org/abs/2304.08069)  
100. DETRs Beat YOLOs on Real-time Object Detection, accessed October 31, 2025, [https://zhao-yian.github.io/RTDETR/](https://zhao-yian.github.io/RTDETR/)  
101. Deformable DETR: Deformable Transformers for End-to-End Object Detection | Request PDF \- ResearchGate, accessed October 31, 2025, [https://www.researchgate.net/publication/344551949\_Deformable\_DETR\_Deformable\_Transformers\_for\_End-to-End\_Object\_Detection](https://www.researchgate.net/publication/344551949_Deformable_DETR_Deformable_Transformers_for_End-to-End_Object_Detection)  
102. DETRs with Collaborative Hybrid Assignments Training | by Tanya Soni \- Medium, accessed October 31, 2025, [https://medium.com/@arithmancylabs/detrs-with-collaborative-hybrid-assignments-training-d3a507738a9d](https://medium.com/@arithmancylabs/detrs-with-collaborative-hybrid-assignments-training-d3a507738a9d)  
103. DETRs with Collaborative Hybrid Assignments Training \- CVF Open Access, accessed October 31, 2025, [https://openaccess.thecvf.com/content/ICCV2023/papers/Zong\_DETRs\_with\_Collaborative\_Hybrid\_Assignments\_Training\_ICCV\_2023\_paper.pdf](https://openaccess.thecvf.com/content/ICCV2023/papers/Zong_DETRs_with_Collaborative_Hybrid_Assignments_Training_ICCV_2023_paper.pdf)  
104. Co-DETR Object Detection Model: What is, How to Use \- Roboflow, accessed October 31, 2025, [https://roboflow.com/model/co-detr](https://roboflow.com/model/co-detr)  
105. Enhancing DETRs for Small Object Detection via Multi-Scale Refinement and Query-Aided Mining \- GitHub, accessed October 31, 2025, [https://raw.githubusercontent.com/mlresearch/v260/main/assets/fu25a/fu25a.pdf](https://raw.githubusercontent.com/mlresearch/v260/main/assets/fu25a/fu25a.pdf)