import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:labelsure_mobile/core/storage_service.dart';
import 'package:labelsure_mobile/models/inspection.dart';
import 'package:labelsure_mobile/screens/inspection_area_screen.dart';
import 'package:labelsure_mobile/screens/collective_report_screen.dart';

void main() {
  setUp(() {
    StorageService().setAuth(
      'token_test_123',
      UserModel(
        id: 'usr_test',
        username: 'inspector1',
        fullName: 'Inspector R. Sharma',
        email: 'inspector@labelsure.gov.in',
        role: 'INSPECTOR',
        badgeNumber: 'DL-LM-001',
      ),
    );
  });

  testWidgets('Inspection Area Setup Screen Renders Correctly', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: InspectionAreaScreen()));
    await tester.pump();

    expect(find.text('Inspection Center Hub'), findsOneWidget);
    expect(find.text('Inspection Area / Center'), findsOneWidget);
    expect(find.text('Establishment / Center Name *'), findsOneWidget);
    expect(find.text('Start Premise Audit & Sample Products'), findsOneWidget);
  });

  testWidgets('Collective Report Screen Renders Metrics and Statutory Notice', (WidgetTester tester) async {
    final sampleSession = AreaSessionModel(
      id: 'area_test_01',
      sessionNumber: 'AREA-2026-0001',
      establishmentName: 'Metro Mega Mart',
      premiseType: 'RETAIL_SUPERMARKET',
      address: 'Indiranagar 100ft Rd',
      district: 'Bengaluru East',
      inspectorName: 'DL-LM Inspector R. Sharma',
      inspectorBadge: 'DL-LM-001',
      inspectionDate: '07-Sep-2026',
      status: 'ACTIVE',
      complianceVerdict: 'NON_COMPLIANT',
      totalItems: 2,
      compliantItems: 1,
      violationItems: 1,
      reviewItems: 0,
      complianceRate: 50.0,
      items: [
        AreaItemModel(
          id: 'item_1',
          sessionId: 'area_test_01',
          itemIndex: 1,
          commodityName: 'Basmati Rice 5kg',
          brandName: 'Royal Feast',
          mrp: '₹450',
          netQuantity: '5 kg',
          complianceStatus: 'COMPLIANT',
          createdAt: DateTime.now().toIso8601String(),
        ),
        AreaItemModel(
          id: 'item_2',
          sessionId: 'area_test_01',
          itemIndex: 2,
          commodityName: 'Almond Drink 1L',
          brandName: 'NutriPure',
          mrp: '₹180',
          netQuantity: '1 L',
          complianceStatus: 'NON_COMPLIANT',
          violationsList: ['Rule 6(1)(e): Unit sale price not declared'],
          createdAt: DateTime.now().toIso8601String(),
        ),
      ],
    );

    final reportData = {
      'certificate_number': 'LMPC-AREA-CERT-2026-0001',
      'pdf_url': '/storage/reports/collective_report_area_test_01.pdf',
      'pdf_sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    };

    await tester.pumpWidget(MaterialApp(
      home: CollectiveReportScreen(
        session: sampleSession,
        reportData: reportData,
      ),
    ));
    await tester.pump();

    // Verify Title & Header
    expect(find.text('Consolidated Premise Audit Report'), findsOneWidget);
    expect(find.text('GOVERNMENT OF INDIA'), findsOneWidget);
    expect(find.text('Metro Mega Mart'), findsOneWidget);

    // Verify Verdict & Scorecard
    expect(find.text('NON-COMPLIANT — STATUTORY VIOLATIONS DETECTED'), findsOneWidget);
    expect(find.text('50.0%'), findsOneWidget);

    // Verify Items
    expect(find.text('Basmati Rice 5kg'), findsOneWidget);
    expect(find.text('Almond Drink 1L'), findsOneWidget);
    expect(find.text('Rule 6(1)(e): Unit sale price not declared'), findsOneWidget);

    // Verify Buttons
    expect(find.text('Download Consolidated PDF Report'), findsOneWidget);
    expect(find.text('Return to Main Dashboard'), findsOneWidget);
  });
}
