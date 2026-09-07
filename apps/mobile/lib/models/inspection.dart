class UserModel {
  final String id;
  final String username;
  final String fullName;
  final String email;
  final String role;
  final String? badgeNumber;

  UserModel({
    required this.id,
    required this.username,
    required this.fullName,
    required this.email,
    required this.role,
    this.badgeNumber,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] ?? json['user_id'] ?? '',
      username: json['username'] ?? '',
      fullName: json['full_name'] ?? '',
      email: json['email'] ?? '',
      role: json['role'] ?? 'INSPECTOR',
      badgeNumber: json['badge_number'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'full_name': fullName,
      'email': email,
      'role': role,
      'badge_number': badgeNumber,
    };
  }
}

class ProductContextModel {
  final String commodityCategory;
  final bool isFood;
  final bool isImported;
  final String originCountry;
  final String packageType;
  final double? declaredNetQuantity;
  final String? declaredUnit;
  final bool isEcommerce;

  ProductContextModel({
    this.commodityCategory = 'FOOD',
    this.isFood = true,
    this.isImported = false,
    this.originCountry = 'India',
    this.packageType = 'STANDARD',
    this.declaredNetQuantity,
    this.declaredUnit = 'g',
    this.isEcommerce = false,
  });

  factory ProductContextModel.fromJson(Map<String, dynamic> json) {
    return ProductContextModel(
      commodityCategory: json['commodity_category'] ?? 'FOOD',
      isFood: json['is_food'] ?? true,
      isImported: json['is_imported'] ?? false,
      originCountry: json['origin_country'] ?? 'India',
      packageType: json['package_type'] ?? 'STANDARD',
      declaredNetQuantity: (json['declared_net_quantity'] as num?)?.toDouble(),
      declaredUnit: json['declared_unit'],
      isEcommerce: json['is_ecommerce'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'commodity_category': commodityCategory,
      'is_food': isFood,
      'is_imported': isImported,
      'origin_country': originCountry,
      'package_type': packageType,
      'declared_net_quantity': declaredNetQuantity,
      'declared_unit': declaredUnit,
      'is_ecommerce': isEcommerce,
    };
  }
}

class InspectionModel {
  final String id;
  final String inspectionNumber;
  final String commodityName;
  final String? brandName;
  final String status;
  final String complianceStatus;
  final String ruleVersion;
  final int totalImages;
  final String createdAt;
  final bool isSynced;
  final ProductContextModel? context;
  final List<InspectionImageModel> images;
  final List<DeclarationModel> declarations;
  final List<MobileFinding> findings;

  InspectionModel({
    required this.id,
    required this.inspectionNumber,
    required this.commodityName,
    this.brandName,
    required this.status,
    required this.complianceStatus,
    required this.ruleVersion,
    this.totalImages = 0,
    required this.createdAt,
    this.isSynced = false,
    this.context,
    this.images = const [],
    this.declarations = const [],
    this.findings = const [],
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'inspection_number': inspectionNumber,
      'commodity_name': commodityName,
      'brand_name': brandName,
      'status': status,
      'compliance_status': complianceStatus,
      'rule_version': ruleVersion,
      'total_images': totalImages,
      'created_at': createdAt,
      'is_synced': isSynced ? 1 : 0,
    };
  }

  factory InspectionModel.fromMap(Map<String, dynamic> map) {
    return InspectionModel(
      id: map['id'] ?? '',
      inspectionNumber: map['inspection_number'] ?? '',
      commodityName: map['commodity_name'] ?? '',
      brandName: map['brand_name'],
      status: map['status'] ?? 'DRAFT',
      complianceStatus: map['compliance_status'] ?? 'PENDING',
      ruleVersion: map['rule_version'] ?? 'LMPC-2026-RULES',
      totalImages: map['total_images'] ?? 0,
      createdAt: map['created_at'] ?? '',
      isSynced: (map['is_synced'] == 1),
    );
  }

  factory InspectionModel.fromJson(Map<String, dynamic> json) {
    var imagesList = <InspectionImageModel>[];
    if (json['images'] != null) {
      imagesList = (json['images'] as List)
          .map((i) => InspectionImageModel.fromJson(i))
          .toList();
    }

    var declList = <DeclarationModel>[];
    if (json['declarations'] != null) {
      declList = (json['declarations'] as List)
          .map((d) => DeclarationModel.fromJson(d))
          .toList();
    }

    var findingsList = <MobileFinding>[];
    if (json['findings'] != null) {
      findingsList = (json['findings'] as List)
          .map((f) => MobileFinding.fromJson(f))
          .toList();
    }

    return InspectionModel(
      id: json['id'] ?? '',
      inspectionNumber: json['inspection_number'] ?? '',
      commodityName: json['commodity_name'] ?? '',
      brandName: json['brand_name'],
      status: json['status'] ?? 'DRAFT',
      complianceStatus: json['compliance_status'] ?? 'PENDING',
      ruleVersion: json['rule_version'] ?? 'LMPC-2026-RULES',
      totalImages: json['total_images'] ?? imagesList.length,
      createdAt: json['created_at'] ?? '',
      isSynced: true,
      context: json['context'] != null ? ProductContextModel.fromJson(json['context']) : null,
      images: imagesList,
      declarations: declList,
      findings: findingsList,
    );
  }
}

class InspectionImageModel {
  final String id;
  final String inspectionId;
  final String viewType;
  final String? localFilePath;
  final String storagePath;
  final String? processedPath;
  final String sha256Hash;
  final int width;
  final int height;
  final bool isAcceptable;
  final double qualityScore;
  final double blurScore;
  final List<String> warnings;

  InspectionImageModel({
    required this.id,
    required this.inspectionId,
    required this.viewType,
    this.localFilePath,
    required this.storagePath,
    this.processedPath,
    required this.sha256Hash,
    required this.width,
    required this.height,
    this.isAcceptable = true,
    this.qualityScore = 1.0,
    this.blurScore = 0.0,
    this.warnings = const [],
  });

  factory InspectionImageModel.fromJson(Map<String, dynamic> json) {
    final q = json['quality_assessment'] ?? {};
    final rawWarnings = q['warnings'] ?? [];
    return InspectionImageModel(
      id: json['id'] ?? '',
      inspectionId: json['inspection_id'] ?? '',
      viewType: json['view_type'] ?? 'FRONT',
      storagePath: json['storage_path'] ?? '',
      processedPath: json['processed_path'],
      sha256Hash: json['sha256_hash'] ?? '',
      width: json['width'] ?? 0,
      height: json['height'] ?? 0,
      isAcceptable: json['is_acceptable'] ?? true,
      qualityScore: (q['quality_score'] as num?)?.toDouble() ?? 1.0,
      blurScore: (q['blur_score'] as num?)?.toDouble() ?? 0.0,
      warnings: List<String>.from(rawWarnings),
    );
  }
}

class DeclarationModel {
  final String id;
  final String? sourceImageId;
  final String category;
  final String rawText;
  final String? unit;
  final double confidence;
  final bool isInspectorEdited;

  DeclarationModel({
    required this.id,
    this.sourceImageId,
    required this.category,
    required this.rawText,
    this.unit,
    this.confidence = 1.0,
    this.isInspectorEdited = false,
  });

  factory DeclarationModel.fromJson(Map<String, dynamic> json) {
    return DeclarationModel(
      id: json['id'] ?? '',
      sourceImageId: json['source_image_id'],
      category: json['category'] ?? '',
      rawText: json['raw_text'] ?? '',
      unit: json['unit'],
      confidence: (json['confidence'] as num?)?.toDouble() ?? 1.0,
      isInspectorEdited: json['is_inspector_edited'] ?? false,
    );
  }
}

class HazardExplanationModel {
  final String detectedIssue;
  final String applicableRule;
  final String reasonForNonCompliance;
  final String consumerHarm;
  final String regulatoryRisk;
  final String evidenceFromPackage;

  HazardExplanationModel({
    required this.detectedIssue,
    required this.applicableRule,
    required this.reasonForNonCompliance,
    required this.consumerHarm,
    required this.regulatoryRisk,
    required this.evidenceFromPackage,
  });

  factory HazardExplanationModel.fromJson(Map<String, dynamic> json) {
    final risks = json['consumer_regulatory_risk'] as Map<String, dynamic>? ?? {};
    return HazardExplanationModel(
      detectedIssue: json['detected_issue'] ?? '',
      applicableRule: json['applicable_rule'] ?? '',
      reasonForNonCompliance: json['reason_for_non_compliance'] ?? '',
      consumerHarm: risks['consumer_harm'] ?? json['consumer_harm'] ?? 'Consumer transparency compromised',
      regulatoryRisk: risks['regulatory_risk'] ?? json['regulatory_risk'] ?? 'Contravention of metrological statute',
      evidenceFromPackage: json['evidence_from_package'] ?? '',
    );
  }
}

class MobileFinding {
  final String id;
  final String ruleId;
  final String clauseReference;
  final String requirementTitle;
  final String aiStatus;
  final String? inspectorStatus;
  final String finalStatus;
  final String severity;
  final String explanation;
  final HazardExplanationModel? hazardExplanation;
  final String? uncertaintyReason;
  final String? observedValue;
  final String expectedCondition;
  final double confidence;
  final String? inspectorComment;
  final List<dynamic> evidenceReferences;

  MobileFinding({
    required this.id,
    required this.ruleId,
    required this.clauseReference,
    required this.requirementTitle,
    required this.aiStatus,
    this.inspectorStatus,
    required this.finalStatus,
    required this.severity,
    required this.explanation,
    this.hazardExplanation,
    this.uncertaintyReason,
    this.observedValue,
    required this.expectedCondition,
    required this.confidence,
    this.inspectorComment,
    this.evidenceReferences = const [],
  });

  factory MobileFinding.fromJson(Map<String, dynamic> json) {
    return MobileFinding(
      id: json['id'] ?? '',
      ruleId: json['rule_id'] ?? '',
      clauseReference: json['clause_reference'] ?? '',
      requirementTitle: json['requirement_title'] ?? '',
      aiStatus: json['ai_status'] ?? 'UNCERTAIN',
      inspectorStatus: json['inspector_status'],
      finalStatus: json['final_status'] ?? 'UNCERTAIN',
      severity: json['severity'] ?? 'HIGH',
      explanation: json['explanation'] ?? '',
      hazardExplanation: json['hazard_explanation'] != null
          ? HazardExplanationModel.fromJson(json['hazard_explanation'])
          : null,
      uncertaintyReason: json['uncertainty_reason'],
      observedValue: json['observed_value'],
      expectedCondition: json['expected_condition'] ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      inspectorComment: json['inspector_comment'],
      evidenceReferences: json['evidence_references'] ?? [],
    );
  }
}

class ReportModel {
  final String id;
  final String inspectionId;
  final String certificateNumber;
  final String generatedBy;
  final String complianceVerdict;
  final String pdfUrl;
  final String pdfSha256;
  final String generatedAt;

  ReportModel({
    required this.id,
    required this.inspectionId,
    required this.certificateNumber,
    required this.generatedBy,
    required this.complianceVerdict,
    required this.pdfUrl,
    required this.pdfSha256,
    required this.generatedAt,
  });

  factory ReportModel.fromJson(Map<String, dynamic> json) {
    return ReportModel(
      id: json['id'] ?? '',
      inspectionId: json['inspection_id'] ?? '',
      certificateNumber: json['certificate_number'] ?? '',
      generatedBy: json['generated_by'] ?? '',
      complianceVerdict: json['compliance_verdict'] ?? 'PENDING',
      pdfUrl: json['pdf_url'] ?? '',
      pdfSha256: json['pdf_sha256'] ?? '',
      generatedAt: json['generated_at'] ?? '',
    );
  }
}

class FollowUpActionModel {
  final String actionType;
  final String statutorySection;
  final String title;
  final String description;
  final String penaltyEstimate;
  final int deadlineDays;
  final String priority;

  FollowUpActionModel({
    required this.actionType,
    required this.statutorySection,
    required this.title,
    required this.description,
    required this.penaltyEstimate,
    required this.deadlineDays,
    this.priority = 'MEDIUM',
  });

  factory FollowUpActionModel.fromJson(Map<String, dynamic> json) {
    return FollowUpActionModel(
      actionType: json['action_type'] ?? '',
      statutorySection: json['statutory_section'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      penaltyEstimate: json['penalty_estimate'] ?? 'NIL',
      deadlineDays: json['deadline_days'] ?? 0,
      priority: json['priority'] ?? 'MEDIUM',
    );
  }
}

class ComprehensiveReportModel {
  final String certificateNumber;
  final String inspectionId;
  final String inspectionNumber;
  final String complianceVerdict;
  final String generatedAt;
  final String generatedBy;
  final String pdfUrl;
  final String pdfSha256;

  // 9 Pillars
  final Map<String, dynamic> productDetails;
  final List<DeclarationModel> extractedDeclarations;
  final List<Map<String, dynamic>> applicableRules;
  final Map<String, dynamic> complianceStatus;
  final List<MobileFinding> detectedViolations;
  final List<InspectionImageModel> visualEvidence;
  final Map<String, dynamic> inspectorVerification;
  final Map<String, dynamic> timestamps;
  final List<FollowUpActionModel> recommendedFollowUpActions;

  ComprehensiveReportModel({
    required this.certificateNumber,
    required this.inspectionId,
    required this.inspectionNumber,
    required this.complianceVerdict,
    required this.generatedAt,
    required this.generatedBy,
    required this.pdfUrl,
    required this.pdfSha256,
    this.productDetails = const {},
    this.extractedDeclarations = const [],
    this.applicableRules = const [],
    this.complianceStatus = const {},
    this.detectedViolations = const [],
    this.visualEvidence = const [],
    this.inspectorVerification = const {},
    this.timestamps = const {},
    this.recommendedFollowUpActions = const [],
  });

  factory ComprehensiveReportModel.fromJson(Map<String, dynamic> json) {
    var decls = <DeclarationModel>[];
    if (json['extracted_declarations'] != null) {
      decls = (json['extracted_declarations'] as List)
          .map((d) => DeclarationModel.fromJson(d))
          .toList();
    }

    var rules = <Map<String, dynamic>>[];
    if (json['applicable_rules'] != null) {
      rules = (json['applicable_rules'] as List)
          .map((r) => Map<String, dynamic>.from(r))
          .toList();
    }

    var violations = <MobileFinding>[];
    if (json['detected_violations'] != null) {
      violations = (json['detected_violations'] as List)
          .map((v) => MobileFinding.fromJson(v))
          .toList();
    }

    var images = <InspectionImageModel>[];
    if (json['visual_evidence'] != null) {
      images = (json['visual_evidence'] as List)
          .map((i) => InspectionImageModel.fromJson(i))
          .toList();
    }

    var actions = <FollowUpActionModel>[];
    if (json['recommended_follow_up_actions'] != null) {
      actions = (json['recommended_follow_up_actions'] as List)
          .map((a) => FollowUpActionModel.fromJson(a))
          .toList();
    }

    return ComprehensiveReportModel(
      certificateNumber: json['certificate_number'] ?? '',
      inspectionId: json['inspection_id'] ?? '',
      inspectionNumber: json['inspection_number'] ?? '',
      complianceVerdict: json['compliance_verdict'] ?? 'PENDING',
      generatedAt: json['generated_at'] ?? '',
      generatedBy: json['generated_by'] ?? 'Legal Metrology Officer',
      pdfUrl: json['pdf_url'] ?? '',
      pdfSha256: json['pdf_sha256'] ?? '',
      productDetails: json['product_details'] != null
          ? Map<String, dynamic>.from(json['product_details'])
          : {},
      extractedDeclarations: decls,
      applicableRules: rules,
      complianceStatus: json['compliance_status'] != null
          ? Map<String, dynamic>.from(json['compliance_status'])
          : {},
      detectedViolations: violations,
      visualEvidence: images,
      inspectorVerification: json['inspector_verification'] != null
          ? Map<String, dynamic>.from(json['inspector_verification'])
          : {},
      timestamps: json['timestamps'] != null
          ? Map<String, dynamic>.from(json['timestamps'])
          : {},
      recommendedFollowUpActions: actions,
    );
  }
}

class AreaItemModel {
  final String id;
  final String sessionId;
  final int itemIndex;
  final String commodityName;
  final String brandName;
  final String mrp;
  final String netQuantity;
  final String complianceStatus; // COMPLIANT, NON_COMPLIANT, REQUIRES_REVIEW
  final List<String> violationsList;
  final String? imagePath;
  final String? imageUrl;
  final double qualityScore;
  final String ocrSnippet;
  final String createdAt;

  AreaItemModel({
    required this.id,
    required this.sessionId,
    required this.itemIndex,
    required this.commodityName,
    required this.brandName,
    required this.mrp,
    required this.netQuantity,
    required this.complianceStatus,
    this.violationsList = const [],
    this.imagePath,
    this.imageUrl,
    this.qualityScore = 1.0,
    this.ocrSnippet = '',
    required this.createdAt,
  });

  factory AreaItemModel.fromJson(Map<String, dynamic> json) {
    var vList = <String>[];
    if (json['violations_list'] != null) {
      vList = List<String>.from(json['violations_list']);
    }
    return AreaItemModel(
      id: json['id'] ?? '',
      sessionId: json['session_id'] ?? '',
      itemIndex: json['item_index'] ?? 1,
      commodityName: json['commodity_name'] ?? 'Packaged Commodity',
      brandName: json['brand_name'] ?? 'Local Pack',
      mrp: json['mrp'] ?? 'Not Declared',
      netQuantity: json['net_quantity'] ?? 'Not Specified',
      complianceStatus: json['compliance_status'] ?? 'PENDING',
      violationsList: vList,
      imagePath: json['image_path'],
      imageUrl: json['image_url'],
      qualityScore: (json['quality_score'] as num?)?.toDouble() ?? 1.0,
      ocrSnippet: json['ocr_snippet'] ?? '',
      createdAt: json['created_at'] ?? '',
    );
  }
}

class AreaSessionModel {
  final String id;
  final String sessionNumber;
  final String establishmentName;
  final String premiseType;
  final String address;
  final String district;
  final String inspectorName;
  final String inspectorBadge;
  final String? notes;
  final String inspectionDate;
  final String status;
  final String complianceVerdict;
  final int totalItems;
  final int compliantItems;
  final int violationItems;
  final int reviewItems;
  final double complianceRate;
  final List<AreaItemModel> items;
  final Map<String, dynamic>? report;

  AreaSessionModel({
    required this.id,
    required this.sessionNumber,
    required this.establishmentName,
    required this.premiseType,
    required this.address,
    required this.district,
    required this.inspectorName,
    required this.inspectorBadge,
    this.notes,
    required this.inspectionDate,
    required this.status,
    required this.complianceVerdict,
    required this.totalItems,
    required this.compliantItems,
    required this.violationItems,
    required this.reviewItems,
    required this.complianceRate,
    this.items = const [],
    this.report,
  });

  factory AreaSessionModel.fromJson(Map<String, dynamic> json) {
    var itemsList = <AreaItemModel>[];
    if (json['items'] != null) {
      itemsList = (json['items'] as List)
          .map((i) => AreaItemModel.fromJson(i))
          .toList();
    }
    return AreaSessionModel(
      id: json['id'] ?? '',
      sessionNumber: json['session_number'] ?? '',
      establishmentName: json['establishment_name'] ?? '',
      premiseType: json['premise_type'] ?? 'RETAIL_SUPERMARKET',
      address: json['address'] ?? '',
      district: json['district'] ?? '',
      inspectorName: json['inspector_name'] ?? '',
      inspectorBadge: json['inspector_badge'] ?? '',
      notes: json['notes'],
      inspectionDate: json['inspection_date'] ?? '',
      status: json['status'] ?? 'ACTIVE',
      complianceVerdict: json['compliance_verdict'] ?? 'PENDING',
      totalItems: json['total_items'] ?? itemsList.length,
      compliantItems: json['compliant_items'] ?? 0,
      violationItems: json['violation_items'] ?? 0,
      reviewItems: json['review_items'] ?? 0,
      complianceRate: (json['compliance_rate'] as num?)?.toDouble() ?? 0.0,
      items: itemsList,
      report: json['report'],
    );
  }
}

class JurisdictionModel {
  final String jurisdictionId;
  final String countryName;
  final String flagEmoji;
  final List<String> regulatoryBodies;
  final List<String> governingActs;
  final int rulesCount;

  JurisdictionModel({
    required this.jurisdictionId,
    required this.countryName,
    required this.flagEmoji,
    this.regulatoryBodies = const [],
    this.governingActs = const [],
    this.rulesCount = 0,
  });

  factory JurisdictionModel.fromJson(Map<String, dynamic> json) {
    return JurisdictionModel(
      jurisdictionId: json['jurisdiction_id'] ?? '',
      countryName: json['country_name'] ?? '',
      flagEmoji: json['flag_emoji'] ?? '🌐',
      regulatoryBodies: json['regulatory_bodies'] != null
          ? List<String>.from(json['regulatory_bodies'])
          : [],
      governingActs: json['governing_acts'] != null
          ? List<String>.from(json['governing_acts'])
          : [],
      rulesCount: json['rules_count'] ?? 0,
    );
  }
}

class CountryBanModel {
  final String jurisdictionId;
  final String countryName;
  final String? regulatoryAgency;
  final String banType;
  final int? banYear;
  final String? legalCitation;
  final String? healthConcern;
  final String? reasonSummary;

  CountryBanModel({
    required this.jurisdictionId,
    required this.countryName,
    this.regulatoryAgency,
    required this.banType,
    this.banYear,
    this.legalCitation,
    this.healthConcern,
    this.reasonSummary,
  });

  factory CountryBanModel.fromJson(Map<String, dynamic> json) {
    return CountryBanModel(
      jurisdictionId: json['jurisdiction_id'] ?? '',
      countryName: json['country_name'] ?? '',
      regulatoryAgency: json['regulatory_agency'],
      banType: json['ban_type'] ?? 'TOTAL_BAN',
      banYear: json['ban_year'],
      legalCitation: json['legal_citation'],
      healthConcern: json['health_concern'],
      reasonSummary: json['reason_summary'],
    );
  }
}

class BannedSubstanceModel {
  final String substanceId;
  final String canonicalName;
  final String matchedTerm;
  final String? category;
  final String? description;
  final bool allowedInIndia;
  final String? indianStatusNote;
  final bool isBannedInTarget;
  final CountryBanModel? targetBanDetail;
  final List<CountryBanModel> allBans;
  final int totalCountriesBanned;

  BannedSubstanceModel({
    required this.substanceId,
    required this.canonicalName,
    required this.matchedTerm,
    this.category,
    this.description,
    required this.allowedInIndia,
    this.indianStatusNote,
    required this.isBannedInTarget,
    this.targetBanDetail,
    this.allBans = const [],
    this.totalCountriesBanned = 0,
  });

  factory BannedSubstanceModel.fromJson(Map<String, dynamic> json) {
    var bansList = <CountryBanModel>[];
    if (json['all_bans'] != null) {
      bansList = (json['all_bans'] as List)
          .map((b) => CountryBanModel.fromJson(b))
          .toList();
    }
    return BannedSubstanceModel(
      substanceId: json['substance_id'] ?? '',
      canonicalName: json['canonical_name'] ?? '',
      matchedTerm: json['matched_term'] ?? '',
      category: json['category'],
      description: json['description'],
      allowedInIndia: json['allowed_in_india'] ?? false,
      indianStatusNote: json['indian_status_note'],
      isBannedInTarget: json['is_banned_in_target'] ?? false,
      targetBanDetail: json['target_ban_detail'] != null
          ? CountryBanModel.fromJson(json['target_ban_detail'])
          : null,
      allBans: bansList,
      totalCountriesBanned: json['total_countries_banned'] ?? bansList.length,
    );
  }
}

class ComparisonMatrixItemModel {
  final String dimension;
  final String title;
  final String comparisonType;
  final String targetRule;
  final String indianRule;
  final String indianLabelStatus;
  final String exportStatus;
  final String severity;
  final String? notes;
  final String? actionRequired;

  ComparisonMatrixItemModel({
    required this.dimension,
    required this.title,
    required this.comparisonType,
    required this.targetRule,
    required this.indianRule,
    required this.indianLabelStatus,
    required this.exportStatus,
    required this.severity,
    this.notes,
    this.actionRequired,
  });

  factory ComparisonMatrixItemModel.fromJson(Map<String, dynamic> json) {
    return ComparisonMatrixItemModel(
      dimension: json['dimension'] ?? '',
      title: json['title'] ?? '',
      comparisonType: json['comparison_type'] ?? 'COMPATIBLE',
      targetRule: json['target_rule'] ?? '',
      indianRule: json['indian_rule'] ?? '',
      indianLabelStatus: json['indian_label_status'] ?? '',
      exportStatus: json['export_status'] ?? 'COMPLIANT',
      severity: json['severity'] ?? 'INFO',
      notes: json['notes'],
      actionRequired: json['action_required'],
    );
  }
}

class InternationalComparisonModel {
  final Map<String, dynamic> jurisdiction;
  final int exportReadinessScore;
  final String overallVerdict;
  final String verdictSummary;
  final String executiveSummary;
  final int totalRequirements;
  final int blockersCount;
  final int warningsCount;
  final List<BannedSubstanceModel> bannedSubstances;
  final List<ComparisonMatrixItemModel> comparisonMatrix;

  InternationalComparisonModel({
    required this.jurisdiction,
    required this.exportReadinessScore,
    required this.overallVerdict,
    required this.verdictSummary,
    required this.executiveSummary,
    required this.totalRequirements,
    required this.blockersCount,
    required this.warningsCount,
    this.bannedSubstances = const [],
    this.comparisonMatrix = const [],
  });

  factory InternationalComparisonModel.fromJson(Map<String, dynamic> json) {
    var bans = <BannedSubstanceModel>[];
    if (json['banned_substances_detected'] != null) {
      bans = (json['banned_substances_detected'] as List)
          .map((b) => BannedSubstanceModel.fromJson(b))
          .toList();
    }
    var matrix = <ComparisonMatrixItemModel>[];
    if (json['comparison_matrix'] != null) {
      matrix = (json['comparison_matrix'] as List)
          .map((m) => ComparisonMatrixItemModel.fromJson(m))
          .toList();
    }
    return InternationalComparisonModel(
      jurisdiction: json['jurisdiction'] != null
          ? Map<String, dynamic>.from(json['jurisdiction'])
          : {},
      exportReadinessScore: json['export_readiness_score'] ?? 100,
      overallVerdict: json['overall_verdict'] ?? 'APPROVED_FOR_EXPORT',
      verdictSummary: json['verdict_summary'] ?? '',
      executiveSummary: json['executive_summary'] ?? '',
      totalRequirements: json['total_requirements'] ?? 0,
      blockersCount: json['blockers_count'] ?? 0,
      warningsCount: json['warnings_count'] ?? 0,
      bannedSubstances: bans,
      comparisonMatrix: matrix,
    );
  }
}

