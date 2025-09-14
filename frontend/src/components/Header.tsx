import { useState, useEffect, useRef } from 'react';
import { User, LogOut, Calculator, Search, UserCheck, Calendar, Building, CreditCard, Command, ArrowRight, Moon, Sun } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from './ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Switch } from './ui/switch';

interface SearchResult {
  id: string;
  title: string;
  subtitle?: string;
  description?: string;
  category: 'patient' | 'doctor' | 'appointment' | 'department' | 'billing';
  module: string;
  data: any;
}

const allSearchData: SearchResult[] = [
  {
    id: 'P-001',
    title: 'John Doe',
    subtitle: 'Male, 45 years',
    description: 'Cardiology patient - Blood type: A+',
    category: 'patient',
    module: 'patients',
    data: { room: 'ICU-12', doctor: 'Dr. Smith', status: 'Admitted' }
  },
  {
    id: 'P-002',
    title: 'Sarah Johnson',
    subtitle: 'Female, 32 years',
    description: 'Pediatrics patient - Blood type: O-',
    category: 'patient',
    module: 'patients',
    data: { room: 'N/A', doctor: 'Dr. Williams', status: 'Outpatient' }
  },
  {
    id: 'D-001',
    title: 'Dr. James Smith',
    subtitle: 'Cardiology',
    description: '15 years experience - Room 301',
    category: 'doctor',
    module: 'doctors',
    data: { department: 'Cardiology', status: 'Available', patientsToday: 12 }
  },
  {
    id: 'D-002',
    title: 'Dr. Sarah Williams',
    subtitle: 'Pediatrics',
    description: '10 years experience - Room 205',
    category: 'doctor',
    module: 'doctors',
    data: { department: 'Pediatrics', status: 'Busy', patientsToday: 18 }
  },
  {
    id: 'APT-001',
    title: 'John Doe - Cardiology Consultation',
    subtitle: 'Today 09:00 AM',
    description: 'Dr. James Smith - Chest pain follow-up',
    category: 'appointment',
    module: 'appointments',
    data: { status: 'Scheduled', priority: 'Normal', duration: '30 mins' }
  },
  {
    id: 'DEPT-001',
    title: 'Emergency Department',
    subtitle: 'Ground Floor - East Wing',
    description: 'Dr. Michael Davis - 24/7 Operations',
    category: 'department',
    module: 'departments',
    data: { occupancy: '80%', staff: '28/35', patients: 45 }
  },
  {
    id: 'INV-001',
    title: 'John Doe - Invoice #INV-001',
    subtitle: '$1,250.00 - Paid',
    description: 'Cardiology Consultation, ECG Test',
    category: 'billing',
    module: 'billing',
    data: { amount: 1250, status: 'Paid', dueDate: '2024-02-28' }
  }
];

interface HeaderProps {
  onModuleChange?: (module: string) => void;
}

// Price estimation data
const serviceCategories = {
  'consultation': {
    name: 'Consultation',
    services: [
      { name: 'General Physician Consultation', price: 500 },
      { name: 'Specialist Consultation', price: 800 },
      { name: 'Cardiologist Consultation', price: 1000 },
      { name: 'Neurologist Consultation', price: 1200 },
      { name: 'Pediatrician Consultation', price: 600 },
      { name: 'Orthopedic Consultation', price: 900 }
    ]
  },
  'diagnostics': {
    name: 'Diagnostic Tests',
    services: [
      { name: 'Blood Test (Complete)', price: 800 },
      { name: 'Urine Analysis', price: 300 },
      { name: 'ECG', price: 400 },
      { name: 'X-Ray (Chest)', price: 600 },
      { name: 'Ultrasound (Abdomen)', price: 1200 },
      { name: 'CT Scan (Head)', price: 3500 },
      { name: 'MRI Scan', price: 8000 },
      { name: 'Echocardiogram', price: 2500 }
    ]
  },
  'procedures': {
    name: 'Minor Procedures',
    services: [
      { name: 'Wound Dressing', price: 200 },
      { name: 'Injection (IM/IV)', price: 150 },
      { name: 'Suture Removal', price: 300 },
      { name: 'Minor Surgery', price: 5000 },
      { name: 'Endoscopy', price: 4000 },
      { name: 'Colonoscopy', price: 6000 }
    ]
  },
  'emergency': {
    name: 'Emergency Services',
    services: [
      { name: 'Emergency Consultation', price: 1500 },
      { name: 'Ambulance Service', price: 2000 },
      { name: 'Emergency Room Visit', price: 3000 },
      { name: 'Oxygen Support (per hour)', price: 500 },
      { name: 'IV Fluids', price: 800 }
    ]
  }
};

export function Header({ onModuleChange }: HeaderProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Price estimation states
  const [isPriceDialogOpen, setIsPriceDialogOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [estimatedTotal, setEstimatedTotal] = useState(0);

  // Dark mode state
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Toggle dark mode
  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    if (!isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const searchData = (searchQuery: string): SearchResult[] => {
    if (!searchQuery.trim()) return [];

    return allSearchData
      .filter(item =>
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.subtitle?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
      .slice(0, 8);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'patient': return User;
      case 'doctor': return UserCheck;
      case 'appointment': return Calendar;
      case 'department': return Building;
      case 'billing': return CreditCard;
      default: return Search;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'patient': return 'bg-blue-100 text-blue-800';
      case 'doctor': return 'bg-green-100 text-green-800';
      case 'appointment': return 'bg-orange-100 text-orange-800';
      case 'department': return 'bg-purple-100 text-purple-800';
      case 'billing': return 'bg-teal-100 text-teal-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  useEffect(() => {
    if (query) {
      const searchResults = searchData(query);
      setResults(searchResults);
      setIsOpen(searchResults.length > 0);
      setSelectedIndex(0);
    } else {
      setResults([]);
      setIsOpen(false);
    }
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => prev < results.length - 1 ? prev + 1 : prev);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => prev > 0 ? prev - 1 : prev);
          break;
        case 'Enter':
          e.preventDefault();
          if (results[selectedIndex]) {
            handleResultClick(results[selectedIndex]);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          inputRef.current?.blur();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, results, selectedIndex]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const handleGlobalKeydown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    document.addEventListener('keydown', handleGlobalKeydown);
    return () => document.removeEventListener('keydown', handleGlobalKeydown);
  }, []);

  const handleResultClick = (result: SearchResult) => {
    if (onModuleChange) {
      onModuleChange(result.module);
    }
    setQuery('');
    setIsOpen(false);
    inputRef.current?.blur();
  };

  // Price estimation functions
  const handleServiceToggle = (serviceName: string, price: number) => {
    setSelectedServices(prev => {
      const isSelected = prev.includes(serviceName);
      const newSelected = isSelected
        ? prev.filter(s => s !== serviceName)
        : [...prev, serviceName];

      // Update total
      const newTotal = newSelected.reduce((total, service) => {
        const allServices = Object.values(serviceCategories).flatMap(cat => cat.services);
        const servicePrice = allServices.find(s => s.name === service)?.price || 0;
        return total + servicePrice;
      }, 0);
      setEstimatedTotal(newTotal);

      return newSelected;
    });
  };

  const resetPriceEstimation = () => {
    setSelectedCategory('');
    setSelectedServices([]);
    setEstimatedTotal(0);
  };

  const handlePriceDialogClose = () => {
    setIsPriceDialogOpen(false);
    resetPriceEstimation();
  };

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4 sticky top-0 z-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 bg-teal-600 rounded-lg flex items-center justify-center">
            <div className="w-6 h-6 bg-white rounded-sm flex items-center justify-center">
              <div className="w-3 h-3 bg-teal-600 rounded-full"></div>
            </div>
          </div>
        </div>

        {/* Global Search */}
        <div ref={searchRef} className="relative w-full max-w-md mx-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              ref={inputRef}
              type="text"
              placeholder="Search patients, doctors, appointments..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => query && setIsOpen(true)}
              className="pl-10 pr-16 bg-gray-50 border-gray-200 focus:bg-white"
            />
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
              <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-xs text-gray-500 bg-gray-100 border border-gray-200 rounded">
                <Command className="h-3 w-3 inline mr-1" />
                K
              </kbd>
            </div>
          </div>

          {/* Search Results Dropdown */}
          {isOpen && results.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
              <div className="p-2">
                <div className="flex items-center justify-between px-3 py-2 text-xs text-gray-500 border-b">
                  <span>{results.length} results found</span>
                  <span>Navigate with ↑↓ • Enter to select</span>
                </div>

                {results.map((result, index) => {
                  const Icon = getCategoryIcon(result.category);
                  return (
                    <button
                      key={result.id}
                      className={`w-full text-left p-3 rounded-lg hover:bg-gray-50 focus:bg-gray-50 focus:outline-none transition-colors ${
                        index === selectedIndex ? 'bg-gray-50' : ''
                      }`}
                      onClick={() => handleResultClick(result)}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 mt-1">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${getCategoryColor(result.category)}`}>
                            <Icon className="h-4 w-4" />
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <p className="text-sm text-gray-900 truncate">{result.title}</p>
                            <Badge variant="outline" className="text-xs">
                              {result.category}
                            </Badge>
                          </div>
                          {result.subtitle && (
                            <p className="text-xs text-gray-600 mb-1">{result.subtitle}</p>
                          )}
                          <p className="text-xs text-gray-500 line-clamp-2">{result.description}</p>
                        </div>
                        <ArrowRight className="h-4 w-4 text-gray-400 flex-shrink-0 mt-1" />
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* No Results */}
          {isOpen && query && results.length === 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
              <div className="p-6 text-center">
                <Search className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">No results found for "{query}"</p>
                <p className="text-xs text-gray-500 mt-1">Try searching for patients, doctors, appointments, or departments</p>
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {/* Dark Mode Toggle */}
          <div className="flex items-center space-x-2">
            <Sun className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            <Switch
              checked={isDarkMode}
              onCheckedChange={toggleDarkMode}
              className="data-[state=checked]:bg-teal-600"
            />
            <Moon className="h-4 w-4 text-gray-500 dark:text-gray-400" />
          </div>

          <Dialog open={isPriceDialogOpen} onOpenChange={setIsPriceDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="bg-teal-50 hover:bg-teal-100 border-teal-200 text-teal-700 dark:bg-teal-900 dark:hover:bg-teal-800 dark:border-teal-600 dark:text-teal-300">
                <Calculator className="h-4 w-4 mr-2" />
                Price Estimation
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2">
                  <Calculator className="h-5 w-5 text-teal-600" />
                  <span>Walk-in Patient Price Estimation</span>
                </DialogTitle>
                <p className="text-sm text-gray-600 mt-2">
                  Get instant price estimates for common hospital services. Select services to calculate total cost.
                </p>
              </DialogHeader>

              <div className="space-y-6">
                {/* Category Selection */}
                <div>
                  <Label>Service Category</Label>
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a service category" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(serviceCategories).map(([key, category]) => (
                        <SelectItem key={key} value={key}>{category.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Services Grid */}
                {selectedCategory && (
                  <div className="space-y-4">
                    <h3 className="text-lg text-gray-900">{serviceCategories[selectedCategory as keyof typeof serviceCategories].name}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {serviceCategories[selectedCategory as keyof typeof serviceCategories].services.map((service) => (
                        <Card
                          key={service.name}
                          className={`cursor-pointer transition-all ${
                            selectedServices.includes(service.name)
                              ? 'ring-2 ring-teal-500 bg-teal-50'
                              : 'hover:bg-gray-50'
                          }`}
                          onClick={() => handleServiceToggle(service.name, service.price)}
                        >
                          <CardContent className="p-4">
                            <div className="flex justify-between items-center">
                              <div>
                                <h4 className="text-sm text-gray-900">{service.name}</h4>
                                <p className="text-xs text-gray-500">Standard rate</p>
                              </div>
                              <div className="text-right">
                                <p className="text-sm text-gray-900">₹{service.price.toLocaleString()}</p>
                                {selectedServices.includes(service.name) && (
                                  <Badge className="mt-1 bg-teal-100 text-teal-800">Selected</Badge>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}

                {/* All Categories View */}
                {!selectedCategory && (
                  <div className="space-y-6">
                    <h3 className="text-lg text-gray-900">Browse All Services</h3>
                    {Object.entries(serviceCategories).map(([key, category]) => (
                      <Card key={key} className="border border-gray-200">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base">{category.name}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {category.services.slice(0, 4).map((service) => (
                              <div
                                key={service.name}
                                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                                  selectedServices.includes(service.name)
                                    ? 'border-teal-500 bg-teal-50'
                                    : 'border-gray-100 hover:bg-gray-50'
                                }`}
                                onClick={() => handleServiceToggle(service.name, service.price)}
                              >
                                <div className="flex justify-between items-center">
                                  <span className="text-sm text-gray-700">{service.name}</span>
                                  <div className="flex items-center space-x-2">
                                    <span className="text-sm text-gray-900">₹{service.price.toLocaleString()}</span>
                                    {selectedServices.includes(service.name) && (
                                      <div className="w-2 h-2 bg-teal-500 rounded-full"></div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          {category.services.length > 4 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="mt-3 text-teal-600 hover:text-teal-700"
                              onClick={() => setSelectedCategory(key)}
                            >
                              View all {category.name.toLowerCase()} ({category.services.length} services)
                            </Button>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}

                {/* Selected Services Summary */}
                {selectedServices.length > 0 && (
                  <Card className="border-teal-200 bg-teal-50">
                    <CardHeader>
                      <CardTitle className="text-base text-teal-800">Price Estimation Summary</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {selectedServices.map((serviceName) => {
                          const allServices = Object.values(serviceCategories).flatMap(cat => cat.services);
                          const service = allServices.find(s => s.name === serviceName);
                          return (
                            <div key={serviceName} className="flex justify-between text-sm">
                              <span className="text-gray-700">{serviceName}</span>
                              <span className="text-gray-900">₹{service?.price.toLocaleString()}</span>
                            </div>
                          );
                        })}
                        <div className="border-t border-teal-200 pt-2 mt-2">
                          <div className="flex justify-between items-center">
                            <span className="text-base text-teal-800">Estimated Total</span>
                            <span className="text-lg text-teal-900">₹{estimatedTotal.toLocaleString()}</span>
                          </div>
                          <p className="text-xs text-teal-600 mt-1">
                            *Prices may vary based on specific requirements and doctor consultation
                          </p>
                        </div>
                      </div>
                      <div className="flex space-x-2 mt-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={resetPriceEstimation}
                        >
                          Clear All
                        </Button>
                        <Button
                          size="sm"
                          className="bg-teal-600 hover:bg-teal-700"
                          onClick={() => {
                            // This could trigger booking or more detailed consultation
                            console.log('Proceed with selected services:', selectedServices);
                          }}
                        >
                          Proceed to Booking
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Disclaimer */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-sm text-blue-800 mb-2">Important Information</h4>
                  <ul className="text-xs text-blue-700 space-y-1">
                    <li>• Prices shown are standard rates and may vary based on individual requirements</li>
                    <li>• Emergency cases may have additional charges</li>
                    <li>• Insurance coverage and discounts are not reflected in these estimates</li>
                    <li>• Final billing will be done after consultation and service completion</li>
                    <li>• For accurate pricing, please consult with our billing department</li>
                  </ul>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center space-x-2 p-2">
                <Avatar className="w-8 h-8">
                  <AvatarImage src="/placeholder-avatar.jpg" />
                  <AvatarFallback className="bg-teal-100 text-teal-700">DR</AvatarFallback>
                </Avatar>
                <div className="text-left">
                  <p className="text-sm text-gray-900">Dr. Sarah Johnson</p>
                  <p className="text-xs text-gray-500">Administrator</p>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem>
                <User className="mr-2 h-4 w-4" />
                Profile Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-600">
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
