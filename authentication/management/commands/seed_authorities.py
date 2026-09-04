from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import User, UserRole, AuthorityProfile, ApprovalStatus


class Command(BaseCommand):
    help = 'Seeds 20 realistic Government Officials and Central Authorities across the 8 North Eastern States'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding 20 Government Officials and Central Authorities for North Eastern Corridors..."))

        # Superadmin for approvals
        superadmin = User.objects.filter(is_superuser=True).first()

        authorities_data = [
            {
                "username": "officer_himanta",
                "email": "himanta.sarma@mdoner.gov.in",
                "first_name": "Dr. Himanta",
                "last_name": "Sarma",
                "phone_number": "+91 94350 11221",
                "official_id": "MDoNER-AS-01",
                "designation": "Nodal Secretary & Regional Coordinator",
                "department_name": "Ministry of Development of North Eastern Region (MDoNER)",
                "jurisdiction_state": "Assam",
                "office_address": "Northeast Council Complex, Nongrim Hills / Guwahati Nodal Cell",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "director_mishra",
                "email": "ak.mishra@sikkim.gov.in",
                "first_name": "Anil Kumar",
                "last_name": "Mishra",
                "phone_number": "+91 94340 33442",
                "official_id": "SSDMA-SK-102",
                "designation": "Director of Relief Operations",
                "department_name": "Sikkim State Disaster Management Authority (SSDMA)",
                "jurisdiction_state": "Sikkim",
                "office_address": "Tashiling Secretariat, Gangtok, Sikkim 737101",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "col_bikram",
                "email": "bikram.das@bro.gov.in",
                "first_name": "Col. Bikram",
                "last_name": "Das",
                "phone_number": "+91 94360 55663",
                "official_id": "BRO-AR-401",
                "designation": "Executive Engineer (Border Corridors)",
                "department_name": "Border Roads Organisation (BRO / Project Vartak)",
                "jurisdiction_state": "Arunachal Pradesh",
                "office_address": "HQ Project Vartak, Tezpur - Bomdila Sector",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "comm_lalremruata",
                "email": "lalremruata@mizoram.gov.in",
                "first_name": "R.",
                "last_name": "Lalremruata",
                "phone_number": "+91 94361 77884",
                "official_id": "MZ-TRANS-09",
                "designation": "Joint Transport Commissioner",
                "department_name": "Transport Department, Government of Mizoram",
                "jurisdiction_state": "Mizoram",
                "office_address": "Mizoram Secretariat, Khatla, Aizawl 796001",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "nodal_biren",
                "email": "biren.singh@manipur.gov.in",
                "first_name": "N. Biren",
                "last_name": "Singh",
                "phone_number": "+91 94362 99005",
                "official_id": "MN-SDMA-22",
                "designation": "State Disaster Logistics Officer",
                "department_name": "Manipur State Disaster Management Authority (MSDMA)",
                "jurisdiction_state": "Manipur",
                "office_address": "Babupara Relief Complex, Imphal 795001",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "dc_tashi",
                "email": "tashi.wangchuk@arunachal.gov.in",
                "first_name": "Tashi",
                "last_name": "Wangchuk",
                "phone_number": "+91 94360 22331",
                "official_id": "IAS-AR-881",
                "designation": "Deputy Commissioner & District Magistrate",
                "department_name": "District Administration, Tawang",
                "jurisdiction_state": "Arunachal Pradesh",
                "office_address": "DC Office, Tawang High Altitude District, 790104",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "super_sangeeta",
                "email": "sangeeta.baruah@gmch.gov.in",
                "first_name": "Dr. Sangeeta",
                "last_name": "Baruah",
                "phone_number": "+91 98640 44552",
                "official_id": "GMCH-AS-301",
                "designation": "Medical Logistics Superintendent",
                "department_name": "Guwahati Medical College & Hospital (GMCH)",
                "jurisdiction_state": "Assam",
                "office_address": "GMCH Complex, Bhangagarh, Guwahati 781032",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "rel_sangma",
                "email": "k.sangma@meghalaya.gov.in",
                "first_name": "K.",
                "last_name": "Sangma",
                "phone_number": "+91 94361 66773",
                "official_id": "ML-SDMA-14",
                "designation": "State Relief Commissioner",
                "department_name": "Meghalaya State Disaster Management Authority",
                "jurisdiction_state": "Meghalaya",
                "office_address": "Additional Secretariat Building, Shillong 793001",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "ddma_temjen",
                "email": "temjen.imchen@nagaland.gov.in",
                "first_name": "Temjen",
                "last_name": "Imchen",
                "phone_number": "+91 94360 88994",
                "official_id": "NL-DDMA-07",
                "designation": "District Disaster Coordinator",
                "department_name": "District Disaster Management Authority, Kohima",
                "jurisdiction_state": "Nagaland",
                "office_address": "DC Office Complex, Kohima 797001",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "dir_debbarma",
                "email": "pradip.debbarma@tripura.gov.in",
                "first_name": "Pradip",
                "last_name": "Debbarma",
                "phone_number": "+91 94361 11225",
                "official_id": "TR-TRANS-18",
                "designation": "Director of Logistics & Operations",
                "department_name": "Tripura Road Transport Corporation (TRTC)",
                "jurisdiction_state": "Tripura",
                "office_address": "TRTC Complex, Krishnanagar, Agartala 799001",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "col_bhattacharya",
                "email": "rajiv.bhattacharya@bro.gov.in",
                "first_name": "Col. Rajiv",
                "last_name": "Bhattacharya",
                "phone_number": "+91 94350 33446",
                "official_id": "BRO-PUSH-55",
                "designation": "Task Force Commander (Barak Valley Corridor)",
                "department_name": "Border Roads Organisation (Project Pushpak)",
                "jurisdiction_state": "Assam",
                "office_address": "HQ Project Pushpak, Silchar - Aizawl Highway Sector",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "cmd_chetia",
                "email": "deepak.chetia@assam.gov.in",
                "first_name": "Deepak",
                "last_name": "Chetia",
                "phone_number": "+91 94351 55667",
                "official_id": "SDRF-AS-11",
                "designation": "Battalion Commander (Flood Relief)",
                "department_name": "State Disaster Response Force (SDRF Assam)",
                "jurisdiction_state": "Assam",
                "office_address": "SDRF Battalion HQ, Dergaon / Silchar Forward Base",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "chief_bhutia",
                "email": "karma.bhutia@sikkim.gov.in",
                "first_name": "Karma",
                "last_name": "Bhutia",
                "phone_number": "+91 94341 77888",
                "official_id": "SK-PWD-82",
                "designation": "Superintending Highway Engineer",
                "department_name": "Sikkim Public Works Department (Roads & Bridges)",
                "jurisdiction_state": "Sikkim",
                "office_address": "PWD Division Office, Mangan District, North Sikkim",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "ig_chhetri",
                "email": "sunil.chhetri@ndrf.gov.in",
                "first_name": "Sunil",
                "last_name": "Chhetri",
                "phone_number": "+91 94352 99009",
                "official_id": "NDRF-NER-01",
                "designation": "Deputy Inspector General (Northeast Command)",
                "department_name": "National Disaster Response Force (1st Bn NDRF)",
                "jurisdiction_state": "Assam",
                "office_address": "Patgaon, Rani, Kamrup Rural, Guwahati 781017",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "dc_lalnunmawia",
                "email": "lalnunmawia@mizoram.gov.in",
                "first_name": "Lalnunmawia",
                "last_name": "Ralte",
                "phone_number": "+91 94363 22330",
                "official_id": "MZ-DIST-44",
                "designation": "District Magistrate & Collector",
                "department_name": "Lunglei District Administration",
                "jurisdiction_state": "Mizoram",
                "office_address": "DC Office Complex, Lunglei 796701",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "nodal_chinglen",
                "email": "chinglen.meitei@rims.edu.in",
                "first_name": "Chinglen",
                "last_name": "Meitei",
                "phone_number": "+91 94364 44551",
                "official_id": "RIMS-MN-90",
                "designation": "Supply Chain Nodal Officer",
                "department_name": "Regional Institute of Medical Sciences (RIMS)",
                "jurisdiction_state": "Manipur",
                "office_address": "RIMS Hospital Complex, Lamphelpat, Imphal 795004",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "md_hazarika",
                "email": "rituraj.hazarika@astc.assam.gov.in",
                "first_name": "Rituraj",
                "last_name": "Hazarika",
                "phone_number": "+91 94353 66772",
                "official_id": "ASTC-HQ-03",
                "designation": "Managing Director",
                "department_name": "Assam State Transport Corporation (ASTC)",
                "jurisdiction_state": "Assam",
                "office_address": "Paltan Bazar, Guwahati 781008",
                "status": ApprovalStatus.APPROVED,
            },
            {
                "username": "officer_pema",
                "email": "pema.dorjee@arunachal.gov.in",
                "first_name": "Pema",
                "last_name": "Dorjee",
                "phone_number": "+91 94365 88993",
                "official_id": "AR-DIST-71",
                "designation": "District Logistics Officer",
                "department_name": "West Kameng District Administration",
                "jurisdiction_state": "Arunachal Pradesh",
                "office_address": "DC Office, Bomdila, West Kameng 790001",
                "status": ApprovalStatus.PENDING,
            },
            {
                "username": "dir_imsong",
                "email": "imsong.ao@nagaland.gov.in",
                "first_name": "Imsong",
                "last_name": "Ao",
                "phone_number": "+91 94366 11224",
                "official_id": "NL-FCS-33",
                "designation": "Deputy Director of Civil Supplies",
                "department_name": "Food & Civil Supplies Department",
                "jurisdiction_state": "Nagaland",
                "office_address": "Dimapur Supply Depot & Logistics Hub, 797112",
                "status": ApprovalStatus.PENDING,
            },
            {
                "username": "sdm_subhashish",
                "email": "subhashish.roy@assam.gov.in",
                "first_name": "Subhashish",
                "last_name": "Roy",
                "phone_number": "+91 94354 33445",
                "official_id": "AS-DIST-99",
                "designation": "Sub-Divisional Magistrate (Emergency Dispatch)",
                "department_name": "Cachar District Administration, Silchar",
                "jurisdiction_state": "Assam",
                "office_address": "DC Office Complex, Silchar, Cachar, Assam 788001",
                "status": ApprovalStatus.PENDING,
            },
        ]

        created_count = 0
        updated_count = 0

        for item in authorities_data:
            user, created = User.objects.get_or_create(
                username=item["username"],
                defaults={
                    "email": item["email"],
                    "first_name": item["first_name"],
                    "last_name": item["last_name"],
                    "role": UserRole.ADMIN,
                    "phone_number": item["phone_number"],
                    "organization": item["department_name"],
                    "is_staff": (item["status"] == ApprovalStatus.APPROVED),
                }
            )

            if created:
                user.set_password("authority123")
                user.save()

            profile, prof_created = AuthorityProfile.objects.get_or_create(
                user=user,
                defaults={
                    "official_id": item["official_id"],
                    "designation": item["designation"],
                    "department_name": item["department_name"],
                    "jurisdiction_state": item["jurisdiction_state"],
                    "office_address": item["office_address"],
                    "approval_status": item["status"],
                    "approved_by": superadmin if item["status"] == ApprovalStatus.APPROVED else None,
                    "approved_at": timezone.now() if item["status"] == ApprovalStatus.APPROVED else None,
                }
            )

            if not prof_created:
                profile.approval_status = item["status"]
                profile.save()
                updated_count += 1
            else:
                created_count += 1

            badge = "[APPROVED]" if item["status"] == ApprovalStatus.APPROVED else "[PENDING]"
            self.stdout.write(f"  {badge} {item['designation']} - {item['first_name']} {item['last_name']} ({item['jurisdiction_state']})")

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully populated 20 Government Officials! ({created_count} created, {updated_count} updated)"))
