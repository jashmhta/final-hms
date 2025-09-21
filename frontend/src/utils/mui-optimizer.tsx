// Optimized Material-UI imports for better tree shaking
export const Box = (props: any) => {
  // Dynamic import for Box component
  return import('@mui/material/Box').then(({ default: Box }) => <Box {...props} />)
}

export const Typography = (props: any) => {
  return import('@mui/material/Typography').then(({ default: Typography }) => <Typography {...props} />)
}

export const Button = (props: any) => {
  return import('@mui/material/Button').then(({ default: Button }) => <Button {...props} />)
}

export const Card = (props: any) => {
  return import('@mui/material/Card').then(({ default: Card }) => <Card {...props} />)
}

export const CardContent = (props: any) => {
  return import('@mui/material/CardContent').then(({ default: CardContent }) => <CardContent {...props} />)
}

export const CircularProgress = (props: any) => {
  return import('@mui/material/CircularProgress').then(({ default: CircularProgress }) => <CircularProgress {...props} />)
}

export const Dialog = (props: any) => {
  return import('@mui/material/Dialog').then(({ default: Dialog }) => <Dialog {...props} />)
}

export const DialogTitle = (props: any) => {
  return import('@mui/material/DialogTitle').then(({ default: DialogTitle }) => <DialogTitle {...props} />)
}

export const DialogContent = (props: any) => {
  return import('@mui/material/DialogContent').then(({ default: DialogContent }) => <DialogContent {...props} />)
}

export const DialogActions = (props: any) => {
  return import('@mui/material/DialogActions').then(({ default: DialogActions }) => <DialogActions {...props} />)
}

export const Grid = (props: any) => {
  return import('@mui/material/Grid').then(({ default: Grid }) => <Grid {...props} />)
}

export const TextField = (props: any) => {
  return import('@mui/material/TextField').then(({ default: TextField }) => <TextField {...props} />)
}

export const Select = (props: any) => {
  return import('@mui/material/Select').then(({ default: Select }) => <Select {...props} />)
}

export const MenuItem = (props: any) => {
  return import('@mui/material/MenuItem').then(({ default: MenuItem }) => <MenuItem {...props} />)
}

export const IconButton = (props: any) => {
  return import('@mui/material/IconButton').then(({ default: IconButton }) => <IconButton {...props} />)
}

export const Tooltip = (props: any) => {
  return import('@mui/material/Tooltip').then(({ default: Tooltip }) => <Tooltip {...props} />)
}

export const Paper = (props: any) => {
  return import('@mui/material/Paper').then(({ default: Paper }) => <Paper {...props} />)
}

export const Table = (props: any) => {
  return import('@mui/material/Table').then(({ default: Table }) => <Table {...props} />)
}

export const TableBody = (props: any) => {
  return import('@mui/material/TableBody').then(({ default: TableBody }) => <TableBody {...props} />)
}

export const TableCell = (props: any) => {
  return import('@mui/material/TableCell').then(({ default: TableCell }) => <TableCell {...props} />)
}

export const TableContainer = (props: any) => {
  return import('@mui/material/TableContainer').then(({ default: TableContainer }) => <TableContainer {...props} />)
}

export const TableHead = (props: any) => {
  return import('@mui/material/TableHead').then(({ default: TableHead }) => <TableHead {...props} />)
}

export const TableRow = (props: any) => {
  return import('@mui/material/TableRow').then(({ default: TableRow }) => <TableRow {...props} />)
}

export const Badge = (props: any) => {
  return import('@mui/material/Badge').then(({ default: Badge }) => <Badge {...props} />)
}

export const Avatar = (props: any) => {
  return import('@mui/material/Avatar').then(({ default: Avatar }) => <Avatar {...props} />)
}

export const Chip = (props: any) => {
  return import('@mui/material/Chip').then(({ default: Chip }) => <Chip {...props} />)
}

export const Divider = (props: any) => {
  return import('@mui/material/Divider').then(({ default: Divider }) => <Divider {...props} />)
}

export const List = (props: any) => {
  return import('@mui/material/List').then(({ default: List }) => <List {...props} />)
}

export const ListItem = (props: any) => {
  return import('@mui/material/ListItem').then(({ default: ListItem }) => <ListItem {...props} />)
}

export const ListItemText = (props: any) => {
  return import('@mui/material/ListItemText').then(({ default: ListItemText }) => <ListItemText {...props} />)
}

export const Snackbar = (props: any) => {
  return import('@mui/material/Snackbar').then(({ default: Snackbar }) => <Snackbar {...props} />)
}

export const Alert = (props: any) => {
  return import('@mui/material/Alert').then(({ default: Alert }) => <Alert {...props} />)
}

export const Tabs = (props: any) => {
  return import('@mui/material/Tabs').then(({ default: Tabs }) => <Tabs {...props} />)
}

export const Tab = (props: any) => {
  return import('@mui/material/Tab').then(({ default: Tab }) => <Tab {...props} />)
}

export const AppBar = (props: any) => {
  return import('@mui/material/AppBar').then(({ default: AppBar }) => <AppBar {...props} />)
}

export const Toolbar = (props: any) => {
  return import('@mui/material/Toolbar').then(({ default: Toolbar }) => <Toolbar {...props} />)
}

export const Menu = (props: any) => {
  return import('@mui/material/Menu').then(({ default: Menu }) => <Menu {...props} />)
}

export const MenuItemMUI = (props: any) => {
  return import('@mui/material/MenuItem').then(({ default: MenuItem }) => <MenuItem {...props} />)
}

export const FormControl = (props: any) => {
  return import('@mui/material/FormControl').then(({ default: FormControl }) => <FormControl {...props} />)
}

export const InputLabel = (props: any) => {
  return import('@mui/material/InputLabel').then(({ default: InputLabel }) => <InputLabel {...props} />)
}

export const FormHelperText = (props: any) => {
  return import('@mui/material/FormHelperText').then(({ default: FormHelperText }) => <FormHelperText {...props} />)
}

export const Checkbox = (props: any) => {
  return import('@mui/material/Checkbox').then(({ default: Checkbox }) => <Checkbox {...props} />)
}

export const Radio = (props: any) => {
  return import('@mui/material/Radio').then(({ default: Radio }) => <Radio {...props} />)
}

export const RadioGroup = (props: any) => {
  return import('@mui/material/RadioGroup').then(({ default: RadioGroup }) => <RadioGroup {...props} />)
}

export const FormControlLabel = (props: any) => {
  return import('@mui/material/FormControlLabel').then(({ default: FormControlLabel }) => <FormControlLabel {...props} />)
}

export const Switch = (props: any) => {
  return import('@mui/material/Switch').then(({ default: Switch }) => <Switch {...props} />)
}

export const Slider = (props: any) => {
  return import('@mui/material/Slider').then(({ default: Slider }) => <Slider {...props} />)
}

export const Rating = (props: any) => {
  return import('@mui/material/Rating').then(({ default: Rating }) => <Rating {...props} />)
}

export const Stepper = (props: any) => {
  return import('@mui/material/Stepper').then(({ default: Stepper }) => <Stepper {...props} />)
}

export const Step = (props: any) => {
  return import('@mui/material/Step').then(({ default: Step }) => <Step {...props} />)
}

export const StepLabel = (props: any) => {
  return import('@mui/material/StepLabel').then(({ default: StepLabel }) => <StepLabel {...props} />)
}

export const StepContent = (props: any) => {
  return import('@mui/material/StepContent').then(({ default: StepContent }) => <StepContent {...props} />)
}

export const Accordion = (props: any) => {
  return import('@mui/material/Accordion').then(({ default: Accordion }) => <Accordion {...props} />)
}

export const AccordionSummary = (props: any) => {
  return import('@mui/material/AccordionSummary').then(({ default: AccordionSummary }) => <AccordionSummary {...props} />)
}

export const AccordionDetails = (props: any) => {
  return import('@mui/material/AccordionDetails').then(({ default: AccordionDetails }) => <AccordionDetails {...props} />)
}

export const Pagination = (props: any) => {
  return import('@mui/material/Pagination').then(({ default: Pagination }) => <Pagination {...props} />)
}

export const TablePagination = (props: any) => {
  return import('@mui/material/TablePagination').then(({ default: TablePagination }) => <TablePagination {...props} />)
}

export const TableSortLabel = (props: any) => {
  return import('@mui/material/TableSortLabel').then(({ default: TableSortLabel }) => <TableSortLabel {...props} />)
}

export const Backdrop = (props: any) => {
  return import('@mui/material/Backdrop').then(({ default: Backdrop }) => <Backdrop {...props} />)
}

export const CircularProgressMUI = (props: any) => {
  return import('@mui/material/CircularProgress').then(({ default: CircularProgress }) => <CircularProgress {...props} />)
}

export const LinearProgress = (props: any) => {
  return import('@mui/material/LinearProgress').then(({ default: LinearProgress }) => <LinearProgress {...props} />)
}

export const Skeleton = (props: any) => {
  return import('@mui/material/Skeleton').then(({ default: Skeleton }) => <Skeleton {...props} />)
}

// Icons optimization
export const Icon = (props: any) => {
  return import('@mui/icons-material').then(({ default: Icon }) => <Icon {...props} />)
}

// Common icon imports optimized
export const SearchIcon = (props: any) => {
  return import('@mui/icons-material/Search').then(({ default: SearchIcon }) => <SearchIcon {...props} />)
}

export const AddIcon = (props: any) => {
  return import('@mui/icons-material/Add').then(({ default: AddIcon }) => <AddIcon {...props} />)
}

export const EditIcon = (props: any) => {
  return import('@mui/icons-material/Edit').then(({ default: EditIcon }) => <EditIcon {...props} />)
}

export const DeleteIcon = (props: any) => {
  return import('@mui/icons-material/Delete').then(({ default: DeleteIcon }) => <DeleteIcon {...props} />)
}

export const SaveIcon = (props: any) => {
  return import('@mui/icons-material/Save').then(({ default: SaveIcon }) => <SaveIcon {...props} />)
}

export const CancelIcon = (props: any) => {
  return import('@mui/icons-material/Cancel').then(({ default: CancelIcon }) => <CancelIcon {...props} />)
}

export const CloseIcon = (props: any) => {
  return import('@mui/icons-material/Close').then(({ default: CloseIcon }) => <CloseIcon {...props} />)
}

export const MenuIcon = (props: any) => {
  return import('@mui/icons-material/Menu').then(({ default: MenuIcon }) => <MenuIcon {...props} />)
}

export const AccountCircleIcon = (props: any) => {
  return import('@mui/icons-material/AccountCircle').then(({ default: AccountCircleIcon }) => <AccountCircleIcon {...props} />)
}

export const NotificationsIcon = (props: any) => {
  return import('@mui/icons-material/Notifications').then(({ default: NotificationsIcon }) => <NotificationsIcon {...props} />)
}

export const SettingsIcon = (props: any) => {
  return import('@mui/icons-material/Settings').then(({ default: SettingsIcon }) => <SettingsIcon {...props} />)
}

export const HelpIcon = (props: any) => {
  return import('@mui/icons-material/Help').then(({ default: HelpIcon }) => <HelpIcon {...props} />)
}

export const InfoIcon = (props: any) => {
  return import('@mui/icons-material/Info').then(({ default: InfoIcon }) => <InfoIcon {...props} />)
}

export const WarningIcon = (props: any) => {
  return import('@mui/icons-material/Warning').then(({ default: WarningIcon }) => <WarningIcon {...props} />)
}

export const ErrorIcon = (props: any) => {
  return import('@mui/icons-material/Error').then(({ default: ErrorIcon }) => <ErrorIcon {...props} />)
}

export const SuccessIcon = (props: any) => {
  return import('@mui/icons-material/CheckCircle').then(({ default: SuccessIcon }) => <SuccessIcon {...props} />)
}

// Healthcare-specific icons
export const MedicalIcon = (props: any) => {
  return import('@mui/icons-material/MedicalServices').then(({ default: MedicalIcon }) => <MedicalIcon {...props} />)
}

export const PatientIcon = (props: any) => {
  return import('@mui/icons-material/Person').then(({ default: PatientIcon }) => <PatientIcon {...props} />)
}

export const CalendarIcon = (props: any) => {
  return import('@mui/icons-material/CalendarToday').then(({ default: CalendarIcon }) => <CalendarIcon {...props} />)
}

export const TimeIcon = (props: any) => {
  return import('@mui/icons-material/Schedule').then(({ default: TimeIcon }) => <TimeIcon {...props} />)
}

export const LocationIcon = (props: any) => {
  return import('@mui/icons-material/LocationOn').then(({ default: LocationIcon }) => <LocationIcon {...props} />)
}

export const PhoneIcon = (props: any) => {
  return import('@mui/icons-material/Phone').then(({ default: PhoneIcon }) => <PhoneIcon {...props} />)
}

export const EmailIcon = (props: any) => {
  return import('@mui/icons-material/Email').then(({ default: EmailIcon }) => <EmailIcon {...props} />)
}

export const HomeIcon = (props: any) => {
  return import('@mui/icons-material/Home').then(({ default: HomeIcon }) => <HomeIcon {...props} />)
}

export const DashboardIcon = (props: any) => {
  return import('@mui/icons-material/Dashboard').then(({ default: DashboardIcon }) => <DashboardIcon {...props} />)
}

export const AnalyticsIcon = (props: any) => {
  return import('@mui/icons-material/Analytics').then(({ default: AnalyticsIcon }) => <AnalyticsIcon {...props} />)
}

export const ReportIcon = (props: any) => {
  return import('@mui/icons-material/Assessment').then(({ default: ReportIcon }) => <ReportIcon {...props} />)
}

export const SecurityIcon = (props: any) => {
  return import('@mui/icons-material/Security').then(({ default: SecurityIcon }) => <SecurityIcon {...props} />)
}

export const BackupIcon = (props: any) => {
  return import('@mui/icons-material/Backup').then(({ default: BackupIcon }) => <BackupIcon {...props} />)
}

export const CloudIcon = (props: any) => {
  return import('@mui/icons-material/Cloud').then(({ default: CloudIcon }) => <CloudIcon {...props} />)
}

export const DownloadIcon = (props: any) => {
  return import('@mui/icons-material/Download').then(({ default: DownloadIcon }) => <DownloadIcon {...props} />)
}

export const UploadIcon = (props: any) => {
  return import('@mui/icons-material/Upload').then(({ default: UploadIcon }) => <UploadIcon {...props} />)
}

export const PrintIcon = (props: any) => {
  return import('@mui/icons-material/Print').then(({ default: PrintIcon }) => <PrintIcon {...props} />)
}

export const ShareIcon = (props: any) => {
  return import('@mui/icons-material/Share').then(({ default: ShareIcon }) => <ShareIcon {...props} />)
}

export const FavoriteIcon = (props: any) => {
  return import('@mui/icons-material/Favorite').then(({ default: FavoriteIcon }) => <FavoriteIcon {...props} />)
}

export const StarIcon = (props: any) => {
  return import('@mui/icons-material/Star').then(({ default: StarIcon }) => <StarIcon {...props} />)
}

export const FlagIcon = (props: any) => {
  return import('@mui/icons-material/Flag').then(({ default: FlagIcon }) => <FlagIcon {...props} />)
}

export const BookIcon = (props: any) => {
  return import('@mui/icons-material/Book').then(({ default: BookIcon }) => <BookIcon {...props} />)
}

export const LibraryBooksIcon = (props: any) => {
  return import('@mui/icons-material/LibraryBooks').then(({ default: LibraryBooksIcon }) => <LibraryBooksIcon {...props} />)
}

export const HistoryIcon = (props: any) => {
  return import('@mui/icons-material/History').then(({ default: HistoryIcon }) => <HistoryIcon {...props} />)
}

export const TimelineIcon = (props: any) => {
  return import('@mui/icons-material/Timeline').then(({ default: TimelineIcon }) => <TimelineIcon {...props} />)
}

export const TrendingUpIcon = (props: any) => {
  return import('@mui/icons-material/TrendingUp').then(({ default: TrendingUpIcon }) => <TrendingUpIcon {...props} />)
}

export const TrendingDownIcon = (props: any) => {
  return import('@mui/icons-material/TrendingDown').then(({ default: TrendingDownIcon }) => <TrendingDownIcon {...props} />)
}

export const ArrowUpIcon = (props: any) => {
  return import('@mui/icons-material/ArrowUpward').then(({ default: ArrowUpIcon }) => <ArrowUpIcon {...props} />)
}

export const ArrowDownIcon = (props: any) => {
  return import('@mui/icons-material/ArrowDownward').then(({ default: ArrowDownIcon }) => <ArrowDownIcon {...props} />)
}

export const RefreshIcon = (props: any) => {
  return import('@mui/icons-material/Refresh').then(({ default: RefreshIcon }) => <RefreshIcon {...props} />)
}

export const SyncIcon = (props: any) => {
  return import('@mui/icons-material/Sync').then(({ default: SyncIcon }) => <SyncIcon {...props} />)
}

export const FilterIcon = (props: any) => {
  return import('@mui/icons-material/FilterList').then(({ default: FilterIcon }) => <FilterIcon {...props} />)
}

export const SortIcon = (props: any) => {
  return import('@mui/icons-material/Sort').then(({ default: SortIcon }) => <SortIcon {...props} />)
}

export const ViewIcon = (props: any) => {
  return import('@mui/icons-material/Visibility').then(({ default: ViewIcon }) => <ViewIcon {...props} />)
}

export const ViewOffIcon = (props: any) => {
  return import('@mui/icons-material/VisibilityOff').then(({ default: ViewOffIcon }) => <ViewOffIcon {...props} />)
}

export const EditNoteIcon = (props: any) => {
  return import('@mui/icons-material/EditNote').then(({ default: EditNoteIcon }) => <EditNoteIcon {...props} />)
}

export const NoteIcon = (props: any) => {
  return import('@mui/icons-material/Note').then(({ default: NoteIcon }) => <NoteIcon {...props} />)
}

export const AssignmentIcon = (props: any) => {
  return import('@mui/icons-material/Assignment').then(({ default: AssignmentIcon }) => <AssignmentIcon {...props} />)
}

export const TaskIcon = (props: any) => {
  return import('@mui/icons-material/Task').then(({ default: TaskIcon }) => <TaskIcon {...props} />)
}

export const ChecklistIcon = (props: any) => {
  return import('@mui/icons-material/Checklist').then(({ default: ChecklistIcon }) => <ChecklistIcon {...props} />)
}

export const VerifiedIcon = (props: any) => {
  return import('@mui/icons-material/Verified').then(({ default: VerifiedIcon }) => <VerifiedIcon {...props} />)
}

export const VerifiedUserIcon = (props: any) => {
  return import('@mui/icons-material/VerifiedUser').then(({ default: VerifiedUserIcon }) => <VerifiedUserIcon {...props} />)
}

export const SecurityUpdateIcon = (props: any) => {
  return import('@mui/icons-material/SecurityUpdate').then(({ default: SecurityUpdateIcon }) => <SecurityUpdateIcon {...props} />)
}

export const PrivacyTipIcon = (props: any) => {
  return import('@mui/icons-material/PrivacyTip').then(({ default: PrivacyTipIcon }) => <PrivacyTipIcon {...props} />)
}

export const GppGoodIcon = (props: any) => {
  return import('@mui/icons-material/GppGood').then(({ default: GppGoodIcon }) => <GppGoodIcon {...props} />)
}

export const HealthAndSafetyIcon = (props: any) => {
  return import('@mui/icons-material/HealthAndSafety').then(({ default: HealthAndSafetyIcon }) => <HealthAndSafetyIcon {...props} />)
}

export const EmergencyIcon = (props: any) => {
  return import('@mui/icons-material/Emergency').then(({ default: EmergencyIcon }) => <EmergencyIcon {...props} />)
}

export const AmbulanceIcon = (props: any) => {
  return import('@mui/icons-material/Ambulance').then(({ default: AmbulanceIcon }) => <AmbulanceIcon {...props} />)
}

export const MedicalInformationIcon = (props: any) => {
  return import('@mui/icons-material/MedicalInformation').then(({ default: MedicalInformationIcon }) => <MedicalInformationIcon {...props} />)
}

export const MedicationIcon = (props: any) => {
  return import('@mui/icons-material/Medication').then(({ default: MedicationIcon }) => <MedicationIcon {...props} />)
}

export const MonitorHeartIcon = (props: any) => {
  return import('@mui/icons-material/MonitorHeart').then(({ default: MonitorHeartIcon }) => <MonitorHeartIcon {...props} />)
}

export const BloodtypeIcon = (props: any) => {
  return import('@mui/icons-material/Bloodtype').then(({ default: BloodtypeIcon }) => <BloodtypeIcon {...props} />)
}

export const PregnantWomanIcon = (props: any) => {
  return import('@mui/icons-material/PregnantWoman').then(({ default: PregnantWomanIcon }) => <PregnantWomanIcon {...props} />)
}

export const ElderlyIcon = (props: any) => {
  return import('@mui/icons-material/Elderly').then(({ default: ElderlyIcon }) => <ElderlyIcon {...props} />)
}

export const AccessibilityIcon = (props: any) => {
  return import('@mui/icons-material/Accessibility').then(({ default: AccessibilityIcon }) => <AccessibilityIcon {...props} />)
}

export const BabyChangingStationIcon = (props: any) => {
  return import('@mui/icons-material/BabyChangingStation').then(({ default: BabyChangingStationIcon }) => <BabyChangingStationIcon {...props} />)
}

export const ChildCareIcon = (props: any) => {
  return import('@mui/icons-material/ChildCare').then(({ default: ChildCareIcon }) => <ChildCareIcon {...props} />)
}

export const FamilyRestroomIcon = (props: any) => {
  return import('@mui/icons-material/FamilyRestroom').then(({ default: FamilyRestroomIcon }) => <FamilyRestroomIcon {...props} />)
}

export const WomanIcon = (props: any) => {
  return import('@mui/icons-material/Woman').then(({ default: WomanIcon }) => <WomanIcon {...props} />)
}

export const ManIcon = (props: any) => {
  return import('@mui/icons-material/Man').then(({ default: ManIcon }) => <ManIcon {...props} />)
}

export const TransgenderIcon = (props: any) => {
  return import('@mui/icons-material/Transgender').then(({ default: TransgenderIcon }) => <TransgenderIcon {...props} />)
}

export const Diversity3Icon = (props: any) => {
  return import('@mui/icons-material/Diversity3').then(({ default: Diversity3Icon }) => <Diversity3Icon {...props} />)
}